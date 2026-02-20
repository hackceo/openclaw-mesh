#!/bin/bash
#
# OpenClaw A2A Agent 一键部署脚本
# 磊哥专属
# 使用方法: curl -fsSL https://raw.githubusercontent.com/hackceo/openclaw-mesh/main/deploy-agent.sh | sudo bash -s [agent名称] [公网端口]
#
# 示例:
#   curl ... | sudo bash -s agent-b 8001
#   curl ... | sudo bash -s agent-c 8002
#   curl ... | sudo bash -s agent-d 8003
#   curl ... | sudo bash -s agent-e 8004

set -e

# FRP 服务器配置（磊哥的阿里云）
FRP_SERVER="47.253.177.216"
FRP_PORT="7000"
FRP_TOKEN="I2+w1dY53JpR+1xo6cIoBmCsq0pf5CT6E927776A3rI="

# Agent 配置
AGENT_NAME="${1:-agent-$(hostname | md5sum | cut -c1-4)}"
AGENT_PORT="${2:-8001}"
LOCAL_PORT="5001"

echo "============================================================"
echo "  🤖 OpenClaw A2A Agent 一键部署"
echo "============================================================"
echo ""
echo "Agent 名称: $AGENT_NAME"
echo "公网端口: $AGENT_PORT"
echo ""

# 1. 创建目录
mkdir -p /opt/openclaw-agent
cd /opt/openclaw-agent

# 2. 下载并配置 FRP Client
echo "📥 下载 FRP..."
if [ ! -d "frp" ]; then
    wget -q https://github.com/fatedier/frp/releases/download/v0.61.0/frp_0.61.0_linux_amd64.tar.gz
    tar -xzf frp_0.61.0_linux_amd64.tar.gz
    mv frp_0.61.0_linux_amd64 frp
    rm frp_0.61.0_linux_amd64.tar.gz
fi

echo "⚙️  配置 FRP Client..."
cat > frp/frpc.toml << EOF
serverAddr = "$FRP_SERVER"
serverPort = $FRP_PORT
auth.token = "$FRP_TOKEN"

[[proxies]]
name = "$AGENT_NAME"
type = "tcp"
localIP = "127.0.0.1"
localPort = $LOCAL_PORT
remotePort = $AGENT_PORT
EOF

# 3. 启动 FRP
echo "🚀 启动 FRP Client..."
nohup ./frp/frpc -c ./frp/frpc.toml > frpc.log 2>&1 &
echo $! > frpc.pid

# 4. 安装 python-a2a
echo "📦 安装依赖..."
pip3 install python-a2a -q 2>/dev/null || pip install python-a2a -q

# 5. 创建 A2A Agent
echo "🤖 创建 A2A Agent..."
cat > agent.py << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '/opt/openclaw-agent')

try:
    from python_a2a import A2AServer, AgentCard, AgentSkill, Message, TextContent
except:
    print("❌ 请安装: pip3 install python-a2a")
    sys.exit(1)

import os
AGENT_NAME = os.environ.get('AGENT_NAME', 'unnamed-agent')
PUBLIC_URL = os.environ.get('PUBLIC_URL', 'http://localhost:5001')

class OpenClawAgent(A2AServer):
    def __init__(self):
        # 根据名称决定技能
        skills = []
        if "python" in AGENT_NAME or "code" in AGENT_NAME:
            skills.append(AgentSkill(
                id="coding", 
                name="Python编程", 
                description="编写Python代码",
                tags=["python", "coding"]
            ))
        elif "design" in AGENT_NAME or "ui" in AGENT_NAME:
            skills.append(AgentSkill(
                id="design",
                name="UI设计",
                description="界面设计",
                tags=["ui", "design"]
            ))
        else:
            skills.append(AgentSkill(
                id="general",
                name="通用助手",
                description="回答问题",
                tags=["general"]
            ))
        
        super().__init__(AgentCard(
            name=AGENT_NAME,
            description=f"OpenClaw Agent: {AGENT_NAME}",
            url=PUBLIC_URL,
            skills=skills
        ))
    
    async def handle_message(self, message):
        # 获取用户输入
        user_text = ""
        for content in message.content:
            if hasattr(content, 'text'):
                user_text = content.text
                break
        
        # 这里可以接入 OpenClaw
        # 目前简单回复
        response = f"【{AGENT_NAME}】收到消息: {user_text}\n\n"
        response += "我是 OpenClaw A2A Agent，已准备就绪！"
        
        return Message(content=[TextContent(text=response)])

async def main():
    agent = OpenClawAgent()
    print(f"🚀 {AGENT_NAME} 启动在 http://0.0.0.0:5001")
    print(f"🌐 公网访问: {PUBLIC_URL}")
    await agent.run(host="0.0.0.0", port=5001)

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

# 6. 启动 Agent
echo "🚀 启动 A2A Agent..."
export AGENT_NAME="$AGENT_NAME"
export PUBLIC_URL="http://$FRP_SERVER:$AGENT_PORT"
nohup python3 agent.py > agent.log 2>&1 &
echo $! > agent.pid

# 7. 验证
echo ""
echo "============================================================"
echo "  ✅ 部署完成!"
echo "============================================================"
echo ""
echo "Agent 信息:"
echo "  名称: $AGENT_NAME"
echo "  本地: http://127.0.0.1:5001"
echo "  公网: http://$FRP_SERVER:$AGENT_PORT"
echo ""
echo "查看状态:"
echo "  日志: tail -f /opt/openclaw-agent/agent.log"
echo "  FRP日志: tail -f /opt/openclaw-agent/frpc.log"
echo ""
echo "测试命令:"
echo "  curl http://$FRP_SERVER:$AGENT_PORT/.well-known/agent.json"
echo ""
