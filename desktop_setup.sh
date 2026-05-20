#!/bin/bash
# ============================================
# 黑曜桌機開機套件 — 一鍵設定
# 桌機開機 → 自動 SSH 到 VPS → 同步記憶
# 用法: bash desktop_setup.sh
# ============================================
set -e

VPS_HOST="35.187.206.192"
VPS_USER="pop5057273712_gmail_com"
DESKTOP_USER="${USER:-$(whoami)}"

echo "===== 黑曜桌機自動連線設定 ====="
echo "VPS: ${VPS_HOST}"
echo "桌機使用者: ${DESKTOP_USER}"
echo ""

# 1. 設定 SSH config
echo "[1/4] 設定 SSH 自動連線..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/config << 'SSHEOF'

# === 黑曜 VPS ===
Host heiyao-vps
    HostName 35.187.206.192
    User pop5057273712_gmail_com
    ServerAliveInterval 30
    ServerAliveCountMax 3
    TCPKeepAlive yes
    StrictHostKeyChecking accept-new
SSHEOF
chmod 600 ~/.ssh/config

# 2. 複製 VPS 公鑰過來（免密碼登入）
echo "[2/4] 設定免密碼 SSH..."
ssh-copy-id -o StrictHostKeyChecking=accept-new ${VPS_USER}@${VPS_HOST} 2>/dev/null || echo "  (若已有金鑰可跳過)"

# 3. 建立同步腳本
echo "[3/4] 建立記憶同步腳本..."
cat > ~/.heiyao_sync.sh << 'SYNCEOF'
#!/bin/bash
VPS="pop5057273712_gmail_com@35.187.206.192"
scp -q ${VPS}:~/.ai_memory.json ~/  2>/dev/null
scp -q ${VPS}:~/AGENTS.md ~/  2>/dev/null
SYNCEOF
chmod +x ~/.heiyao_sync.sh
~/.heiyao_sync.sh
echo "  首次同步完成"

# 4. 建立 systemd 自動服務（開機就跑）
echo "[4/4] 設定開機自動連線..."
SERVICE_FILE="/etc/systemd/system/heiyao-tunnel.service"
sudo tee "$SERVICE_FILE" > /dev/null << SERVICEEOF
[Unit]
Description=黑曜永久通道 - 開機自動連 VPS
After=network-online.target
Wants=network-online.target

[Service]
User=${DESKTOP_USER}
ExecStartPre=/usr/bin/ssh-keygen -R 35.187.206.192 2>/dev/null; /bin/true
ExecStart=/usr/bin/autossh -M 0 \\
    -o "ServerAliveInterval 30" \\
    -o "ServerAliveCountMax 3" \\
    -o "StrictHostKeyChecking accept-new" \\
    -N heiyao-vps
ExecStartPost=/bin/bash /home/${DESKTOP_USER}/.heiyao_sync.sh
ExecStopPost=/bin/bash /home/${DESKTOP_USER}/.heiyao_sync.sh
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
SERVICEEOF

sudo systemctl daemon-reload
sudo systemctl enable --now heiyao-tunnel.service

echo ""
echo "===== 設定完成 ====="
echo "開機自動連線: sudo systemctl status heiyao-tunnel"
echo "手動同步記憶: bash ~/.heiyao_sync.sh"
echo "下次開機 → 自動 SSH 到 VPS → 自動拉記憶 → opencode 開工"
