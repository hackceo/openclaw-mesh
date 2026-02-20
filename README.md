# OpenClaw 去中心化网络

磊哥专属的 OpenClaw Agent 组网方案

## 这是什么？

一套让 5 个 OpenClaw Agent 自动发现、互相通信的去中心化网络方案。

**核心特点：**
- 🌐 去中心化 - 没有中心服务器，任意一台挂了不影响其他
- 🔍 自动发现 - Agent 启动后自动找到其他 Agent
- 💬 互相通信 - 任意两个 Agent 可以直接对话
- 🚀 一键部署 - 一条命令完成安装

## 快速开始

### 服务器 A（种子节点，第一个启动）

```bash
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-a
```

### 服务器 B/C/D/E（连接到种子）

```bash
# 服务器 B
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-b 100.64.1.1

# 服务器 C
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-c 100.64.1.1

# 服务器 D
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-d 100.64.1.1

# 服务器 E
curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/install.sh | sudo bash -s agent-e 100.64.2.1
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `decentralized_discovery.py` | Gossip 协议核心代码 |
| `install.sh` | 一键安装脚本 |
| `start.sh` | 启动脚本 |

## 技术原理

**Gossip 协议**

就像八卦传播一样：
1. A 认识 B，告诉 B 我还认识 C
2. B 认识 C，告诉 C 我认识 A 和 D
3. 最后所有人都认识了所有人

**去中心化**
- 没有中心注册服务器
- 每个 Agent 都是平等的
- 任意一台挂了，其他照样通信

## 查看状态

```bash
# 查看日志
tail -f /opt/openclaw-mesh/discovery.log

# 查看已知 peers
grep "已知" /opt/openclaw-mesh/discovery.log

# 查看进程
ps aux | grep decentralized
```

## 停止服务

```bash
kill $(cat /opt/openclaw-mesh/discovery.pid)
```

## 作者

磊哥专属 💰
