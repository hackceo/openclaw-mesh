#!/bin/bash
#
# OpenClaw 去中心化网络 - 一键安装脚本
# 从 GitHub 下载并运行
# 磊哥专属
#
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/你的账号/openclaw-mesh/main/install.sh | sudo bash
#

set -e

# 配置
REPO_URL="https://raw.githubusercontent.com/hackceo/openclaw-mesh/main"
INSTALL_DIR="/opt/openclaw-mesh"

echo "============================================================"
echo "  🌐 OpenClaw 去中心化网络 - 一键安装"
echo "============================================================"
echo ""

# 检查 root
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行"
    exit 1
fi

# 获取参数
AGENT_ID="${1:-agent-$(hostname | md5sum | cut -c1-4)}"
SEED_IP="${2:-}"

echo "📋 安装信息:"
echo "  Agent ID: $AGENT_ID"
echo "  种子节点: ${SEED_IP:-无（作为种子启动）}"
echo ""

# 创建目录
echo "📁 创建安装目录..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# 下载核心文件
echo "📥 下载核心文件..."
curl -fsSL -o decentralized_discovery.py "$REPO_URL/decentralized_discovery.py"
curl -fsSL -o start.sh "$REPO_URL/start.sh"
chmod +x start.sh

echo "✅ 下载完成"
echo ""

# 启动
echo "🚀 启动去中心化发现服务..."
./start.sh "$AGENT_ID" "$SEED_IP"

echo ""
echo "============================================================"
echo "  ✅ 安装完成!"
echo "============================================================"
echo ""
echo "查看状态:"
echo "  tail -f $INSTALL_DIR/discovery.log"
echo ""
echo "查看已知 peers:"
echo "  grep '已知' $INSTALL_DIR/discovery.log"
echo ""
echo "停止服务:"
echo "  kill \$(cat $INSTALL_DIR/discovery.pid)"
echo ""
