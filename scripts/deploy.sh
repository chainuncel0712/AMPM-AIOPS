#!/bin/bash
# AMPM-AIOPS 黑曜自動部署腳本
# 由 ServiceAgent InstallAgent 呼叫
# 用法: bash deploy.sh <IP> <USER> <PORT> <LICENSE_KEY>

set -e

IP=$1
USER=$2
PORT=${3:-22}
LICENSE_KEY=$4

if [ -z "$IP" ] || [ -z "$USER" ]; then
    echo "❌ 用法: bash deploy.sh <IP> <USER> [PORT] [LICENSE_KEY]"
    exit 1
fi

echo "=============================="
echo "  AMPM-AIOPS 黑曜自動部署"
echo "  目標: $USER@$IP:$PORT"
echo "  授權: ${LICENSE_KEY:-無}"
echo "=============================="

ssh -o StrictHostKeyChecking=no -p "$PORT" "$USER@$IP" bash -s -- "$LICENSE_KEY" << 'REMOTE'
set -e
KEY=$1

echo "[1/5] 更新系統套件..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl tmux

echo "[2/5] 下載黑曜..."
cd /opt
if [ -d AMPM-AIOPS ]; then
    cd AMPM-AIOPS && git pull
else
    git clone https://github.com/chainuncel0712/AMPM-AIOPS.git
    cd AMPM-AIOPS
fi

echo "[3/5] 設定 Python 環境..."
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

echo "[4/5] 設定授權..."
if [ -n "$KEY" ]; then
    echo "$KEY" > data/license.key
fi

echo "[5/5] 啟動黑曜..."
tmux new-session -d -s obsidian 'cd /opt/AMPM-AIOPS && python3 main.py' 2>/dev/null || \
screen -dmS obsidian bash -c 'cd /opt/AMPM-AIOPS && python3 main.py'

echo "=============================="
echo "  ✅ 部署完成！"
echo "  位置: /opt/AMPM-AIOPS"
echo "  授權: ${KEY:-未設定}"
echo "  查看狀態: tmux attach -t obsidian"
echo "=============================="
REMOTE

echo "✅ 遠端部署指令已執行完畢"
