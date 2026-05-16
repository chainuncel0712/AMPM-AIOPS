#!/bin/bash
# 黑曜機械人守護程序 v5 — 優雅關閉版
set -e

cd "$(dirname "$0")"

LOCKFILE="/tmp/heiyao_daemon.lock"
PIDFILE="/tmp/heiyao_main.pid"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# 單實例鎖定
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${RED}⚠️ 守護程序已在執行 (PID: $OLD_PID)${NC}"
        exit 1
    fi
fi

echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE $PIDFILE; echo '🛑 守護程序已終止'" EXIT

# 優雅關閉函數
graceful_shutdown() {
    echo -e "${YELLOW}⏳ 正在優雅關閉...${NC}"
    if [ -f "$PIDFILE" ]; then
        MAIN_PID=$(cat "$PIDFILE")
        kill -TERM "$MAIN_PID" 2>/dev/null || true
        for i in $(seq 1 10); do
            if ! kill -0 "$MAIN_PID" 2>/dev/null; then break; fi
            sleep 1
        done
        kill -9 "$MAIN_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ 已關閉${NC}"
}

trap graceful_shutdown SIGTERM SIGINT

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 找不到 python3${NC}"
    exit 1
fi

echo ""
echo "============================================"
echo -e "${GREEN}  🤖 黑曜機械人守護程序 v5${NC}"
echo "============================================"
echo -e "${BLUE}  啟動: $(date)${NC}"
echo -e "${BLUE}  目錄: $(pwd)${NC}"
echo -e "${GREEN}  ✅ Python: $(python3 --version)${NC}"
echo ""

# 啟動循環
RETRY=0; MAX_RETRY=999

while [ $RETRY -lt $MAX_RETRY ]; do
    RETRY=$((RETRY + 1))
    echo -e "${GREEN}🚀 第 $RETRY 次啟動...${NC}"

    python3 main.py &
    MAIN_PID=$!
    echo $MAIN_PID > "$PIDFILE"
    echo -e "${BLUE}  PID: $MAIN_PID${NC}"

    wait $MAIN_PID 2>/dev/null || true
    EXIT_CODE=$?

    echo -e "${YELLOW}⚠️ 主程序終止 (Exit: $EXIT_CODE)，5 秒後重啟...${NC}"
    sleep 5
done
