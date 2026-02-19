#!/bin/bash
#
# 启动脚本 - 被 install.sh 调用
#

INSTALL_DIR="/opt/openclaw-mesh"
AGENT_ID="${1:-agent-$(hostname | md5sum | cut -c1-4)}"
SEED_IP="${2:-}"

cd $INSTALL_DIR

# 启动去中心化发现
if [ -z "$SEED_IP" ]; then
    echo "🚀 作为种子节点启动: $AGENT_ID"
    python3 decentralized_discovery.py "$AGENT_ID" >> discovery.log 2>&1 &
else
    echo "🚀 连接到种子节点 $SEED_IP: $AGENT_ID"
    python3 decentralized_discovery.py "$AGENT_ID" "$SEED_IP" >> discovery.log 2>&1 &
fi

PID=$!
echo $PID > discovery.pid

echo "✅ 服务已启动 (PID: $PID)"
echo "📋 Agent ID: $AGENT_ID"
echo "📝 日志: $INSTALL_DIR/discovery.log"
