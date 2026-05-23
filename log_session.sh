#!/bin/bash
# 30秒記錄一次 Session Memory
LOG_FILE="/tmp/session_memory.log"
INTERVAL=30

# 防止重複啟動
LOCKFILE="/tmp/session_memory.lock"
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0
    fi
fi
echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "🚀 Session Memory 記錄器啟動 (間隔 ${INTERVAL}s)"

while true; do
    # 記錄當前時間和一些基本資訊
    log "=== 記錄點 ==="
    
    # 檢查主 Bot 狀態
    if pgrep -f "python3.*main.py" > /dev/null; then
        log "✅ 主 Bot 運行中"
    else
        log "❌ 主 Bot 未運行"
    fi
    
    # 檢查授權數量
    if [ -f "/home/pop5057273712_gmail_com/AMPM-AIOPS/data/licenses.json" ]; then
        count=$(grep -c '"key"' "/home/pop5057273712_gmail_com/AMPM-AIOPS/data/licenses.json" 2>/dev/null || echo "0")
        log "📄 授權數量: $count"
    fi
    
    # 檢環境變數
    if [ -f "/home/pop5057273712_gmail_com/AMPM-AIOPS/.env" ]; then
        if grep -q "BSCSCAN_API_KEY" "/home/pop5057273712_gmail_com/AMPM-AIOPS/.env"; then
            log "🔑 BSCSCAN_API_KEY 已設置"
        else
            log "⚠️ BSCSCAN_API_KEY 未設置"
        fi
    fi
    
    log "=================="
    sleep "$INTERVAL"
done