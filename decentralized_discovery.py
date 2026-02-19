#!/usr/bin/env python3
#
# OpenClaw 去中心化服务发现
# 磊哥专属
# 核心: 没有中心服务器，Agent 之间互相发现
#

import json
import socket
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class AgentInfo:
    """Agent 信息"""
    agent_id: str
    name: str
    role: str
    skills: List[str]
    tailscale_ip: str
    port: int
    token_hash: str  # 只存 hash，不存明文
    status: str
    last_seen: datetime
    version: str = "1.0"

class DecentralizedDiscovery:
    """
    去中心化服务发现
    
    核心机制:
    1. Gossip 协议 - Agent 之间互相传播信息
    2. 广播发现 - 新加入时广播自己的存在
    3. 心跳维护 - 定期更新存活状态
    4. 失效剔除 - 超时未心跳的自动移除
    
    优点: 无单点故障，任意 Agent 挂了不影响其他
    缺点: 信息同步有延迟，网络开销大
    """
    
    def __init__(self, 
                 my_agent: AgentInfo,
                 known_peers: List[str] = None,  # 已知的一些 peer IP
                 gossip_port: int = 9999,
                 heartbeat_interval: int = 10):
        
        self.my_agent = my_agent
        self.gossip_port = gossip_port
        self.heartbeat_interval = heartbeat_interval
        
        # 本地存储所有已知的 Agent
        self.peers: Dict[str, AgentInfo] = {}
        self.peers[my_agent.agent_id] = my_agent  # 把自己也加进去
        
        # 种子节点（启动时连接的已知 Agent）
        self.seed_peers = known_peers or []
        
        # 启动 Gossip 服务
        self.running = True
        self.gossip_thread = threading.Thread(target=self._gossip_server, daemon=True)
        self.gossip_thread.start()
        
        # 启动心跳广播
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        # 加入网络
        self._join_network()
    
    # ==================== Gossip 协议核心 ====================
    
    def _gossip_server(self):
        """启动 Gossip 服务，接收其他 Agent 的消息"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.gossip_port))
        sock.settimeout(1)
        
        print(f"🌐 Gossip 服务启动在端口 {self.gossip_port}")
        
        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                message = json.loads(data.decode())
                self._handle_message(message, addr[0])
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Gossip 错误: {e}")
        
        sock.close()
    
    def _handle_message(self, message: dict, from_ip: str):
        """处理收到的 Gossip 消息"""
        msg_type = message.get("type")
        
        if msg_type == "JOIN":
            # 新 Agent 加入
            agent_data = message["agent"]
            agent = self._dict_to_agent(agent_data)
            self._add_or_update_peer(agent)
            print(f"🟢 发现新 Agent: {agent.name} ({agent.agent_id}) 来自 {from_ip}")
            
            # 回复自己的信息
            self._send_to(agent.tailscale_ip, {
                "type": "JOIN_ACK",
                "agent": self._agent_to_dict(self.my_agent),
                "peers": [self._agent_to_dict(p) for p in self.peers.values()]
            })
        
        elif msg_type == "JOIN_ACK":
            # 收到加入确认，获取对方已知的 peers
            for peer_data in message.get("peers", []):
                peer = self._dict_to_agent(peer_data)
                self._add_or_update_peer(peer)
        
        elif msg_type == "HEARTBEAT":
            # 心跳，更新存活状态
            agent_data = message["agent"]
            agent = self._dict_to_agent(agent_data)
            self._add_or_update_peer(agent)
        
        elif msg_type == "GOSSIP":
            # 传播其他 Agent 的信息
            for peer_data in message.get("peers", []):
                peer = self._dict_to_agent(peer_data)
                if peer.agent_id != self.my_agent.agent_id:
                    self._add_or_update_peer(peer)
        
        elif msg_type == "LEAVE":
            # Agent 主动离开
            agent_id = message["agent_id"]
            if agent_id in self.peers:
                del self.peers[agent_id]
                print(f"🔴 Agent {agent_id} 离开")
    
    def _send_to(self, ip: str, message: dict):
        """发送消息到指定 IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(json.dumps(message).encode(), (ip, self.gossip_port))
            sock.close()
        except Exception as e:
            print(f"发送失败 {ip}: {e}")
    
    def _broadcast(self, message: dict):
        """广播消息给所有已知 peers"""
        for peer in self.peers.values():
            if peer.agent_id != self.my_agent.agent_id:
                self._send_to(peer.tailscale_ip, message)
    
    # ==================== 网络加入与维护 ====================
    
    def _join_network(self):
        """加入去中心化网络"""
        print(f"🚀 {self.my_agent.name} 正在加入网络...")
        
        # 向种子节点广播自己的存在
        join_msg = {
            "type": "JOIN",
            "agent": self._agent_to_dict(self.my_agent),
            "timestamp": datetime.now().isoformat()
        }
        
        for seed_ip in self.seed_peers:
            print(f"  连接种子节点: {seed_ip}")
            self._send_to(seed_ip, join_msg)
        
        # 如果没有种子节点，等待别人发现自己
        if not self.seed_peers:
            print("  没有种子节点，等待被动发现...")
    
    def _heartbeat_loop(self):
        """定期广播心跳"""
        while self.running:
            time.sleep(self.heartbeat_interval)
            
            # 更新自己的心跳时间
            self.my_agent.last_seen = datetime.now()
            self.peers[self.my_agent.agent_id] = self.my_agent
            
            # 广播心跳
            heartbeat_msg = {
                "type": "HEARTBEAT",
                "agent": self._agent_to_dict(self.my_agent)
            }
            self._broadcast(heartbeat_msg)
            
            # 随机选择一些 peer 传播已知的其他 peer（Gossip 传播）
            if len(self.peers) > 1:
                gossip_targets = self._select_random_peers(3)
                for target_ip in gossip_targets:
                    gossip_msg = {
                        "type": "GOSSIP",
                        "peers": [self._agent_to_dict(p) for p in self.peers.values()]
                    }
                    self._send_to(target_ip, gossip_msg)
    
    def _cleanup_loop(self):
        """清理超时未心跳的 peer"""
        while self.running:
            time.sleep(30)
            
            now = datetime.now()
            timeout = timedelta(seconds=self.heartbeat_interval * 3)
            
            to_remove = []
            for agent_id, peer in self.peers.items():
                if agent_id == self.my_agent.agent_id:
                    continue
                if now - peer.last_seen > timeout:
                    to_remove.append(agent_id)
            
            for agent_id in to_remove:
                peer = self.peers.pop(agent_id)
                print(f"🔴 Agent {peer.name} ({agent_id}) 超时离线")
    
    def _select_random_peers(self, count: int) -> List[str]:
        """随机选择一些 peer 的 IP"""
        import random
        other_peers = [p for p in self.peers.values() 
                      if p.agent_id != self.my_agent.agent_id]
        selected = random.sample(other_peers, min(count, len(other_peers)))
        return [p.tailscale_ip for p in selected]
    
    def _add_or_update_peer(self, agent: AgentInfo):
        """添加或更新 peer"""
        if agent.agent_id in self.peers:
            # 更新
            existing = self.peers[agent.agent_id]
            if agent.last_seen > existing.last_seen:
                self.peers[agent.agent_id] = agent
        else:
            # 新增
            self.peers[agent.agent_id] = agent
    
    # ==================== 工具方法 ====================
    
    def _agent_to_dict(self, agent: AgentInfo) -> dict:
        """Agent 转字典"""
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "skills": agent.skills,
            "tailscale_ip": agent.tailscale_ip,
            "port": agent.port,
            "token_hash": agent.token_hash,
            "status": agent.status,
            "last_seen": agent.last_seen.isoformat(),
            "version": agent.version
        }
    
    def _dict_to_agent(self, data: dict) -> AgentInfo:
        """字典转 Agent"""
        return AgentInfo(
            agent_id=data["agent_id"],
            name=data["name"],
            role=data["role"],
            skills=data["skills"],
            tailscale_ip=data["tailscale_ip"],
            port=data.get("port", 18789),
            token_hash=data.get("token_hash", ""),
            status=data.get("status", "online"),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            version=data.get("version", "1.0")
        )
    
    # ==================== 对外 API ====================
    
    def discover(self, skill: str = None, role: str = None) -> List[AgentInfo]:
        """
        发现其他 Agent
        
        使用示例:
            coders = discovery.discover(skill="python")
            masters = discovery.discover(role="master")
        """
        results = []
        for peer in self.peers.values():
            if peer.agent_id == self.my_agent.agent_id:
                continue
            
            if skill and skill not in peer.skills:
                continue
            
            if role and peer.role != role:
                continue
            
            results.append(peer)
        
        return results
    
    def get_peer(self, agent_id: str) -> AgentInfo:
        """获取指定 peer"""
        return self.peers.get(agent_id)
    
    def list_all(self) -> List[AgentInfo]:
        """列出所有已知的 Agent"""
        return list(self.peers.values())
    
    def get_stats(self) -> dict:
        """获取网络统计"""
        others = [p for p in self.peers.values() 
                 if p.agent_id != self.my_agent.agent_id]
        return {
            "my_id": self.my_agent.agent_id,
            "total_known": len(self.peers),
            "other_peers": len(others),
            "known_ips": [p.tailscale_ip for p in others]
        }
    
    def leave(self):
        """优雅离开网络"""
        print(f"👋 {self.my_agent.name} 离开网络")
        self.running = False
        
        leave_msg = {
            "type": "LEAVE",
            "agent_id": self.my_agent.agent_id
        }
        self._broadcast(leave_msg)

# ==================== 使用示例 ====================

if __name__ == "__main__":
    import sys
    
    # 从命令行参数获取身份
    if len(sys.argv) < 2:
        print("用法: python3 decentralized_discovery.py <agent_id> [seed_ip]")
        print("示例:")
        print("  python3 decentralized_discovery.py agent-a")
        print("  python3 decentralized_discovery.py agent-b 100.64.1.1")
        exit(1)
    
    agent_id = sys.argv[1]
    seed_ip = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 根据 agent_id 分配不同的 IP（模拟）
    ip_map = {
        "agent-a": "100.64.1.1",
        "agent-b": "100.64.2.1",
        "agent-c": "100.64.3.1",
        "agent-d": "100.64.4.1",
        "agent-e": "100.64.5.1"
    }
    
    my_ip = ip_map.get(agent_id, "127.0.0.1")
    
    # 创建自己的 Agent 信息
    my_agent = AgentInfo(
        agent_id=agent_id,
        name=f"Agent-{agent_id}",
        role="worker" if agent_id != "agent-a" else "master",
        skills=["python", "coding"] if "b" in agent_id else ["design", "ui"],
        tailscale_ip=my_ip,
        port=18789,
        token_hash="hash_xxx",
        status="online",
        last_seen=datetime.now()
    )
    
    # 启动去中心化发现
    seeds = [seed_ip] if seed_ip else []
    discovery = DecentralizedDiscovery(
        my_agent=my_agent,
        known_peers=seeds,
        gossip_port=9999,
        heartbeat_interval=5
    )
    
    print(f"\n🚀 {my_agent.name} 已启动")
    print(f"IP: {my_ip}")
    print(f"角色: {my_agent.role}")
    print(f"技能: {my_agent.skills}")
    if seeds:
        print(f"种子节点: {seeds}")
    print()
    
    # 模拟运行
    try:
        for i in range(20):
            time.sleep(3)
            
            # 显示当前已知的 peers
            stats = discovery.get_stats()
            print(f"[{i+1}] 已知 {stats['other_peers']} 个 peers: {stats['known_ips']}")
            
            # 尝试发现特定技能的 Agent
            if i == 10:
                print(f"\n🔍 发现 Python 专家:")
                coders = discovery.discover(skill="python")
                for coder in coders:
                    print(f"  • {coder.name} ({coder.tailscale_ip})")
                print()
    
    except KeyboardInterrupt:
        pass
    
    finally:
        discovery.leave()
        print("\n✅ 已退出")
