#!/bin/bash
# 黑曜機械人 — 直接啟動腳本
set -e

cd "$(dirname "$0")"

# 檢查 .env
if [ ! -f .env ]; then
    echo "⚠️ 找不到 .env，建立空白範本"
    cat > .env << 'EOF'
# Telegram
TELEGRAM_TOKEN_OBSIDIAN=
AUTHORIZED_USER_IDS=
# LLM API
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
EOF
    echo "請編輯 .env 填入金鑰後再執行"
    exit 1
fi

# 檢查 venv
if [ ! -d venv ]; then
    echo "🔧 建立虛擬環境..."
    python3 -m venv venv
fi

source venv/bin/activate

# 安裝依賴
pip install -q -r requirements.txt 2>/dev/null || true

echo "🚀 啟動黑曜機械人..."
python3 main.py
