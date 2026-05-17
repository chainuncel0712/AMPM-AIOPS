#!/bin/bash
# 黑曜守護程序 v6 — 心跳檢測 + 智慧退避 + 防打架
set -e

cd "$(dirname "$0")"

LOCKFILE="/tmp/heiyao_daemon.lock"
PIDFILE="/tmp/heiyao_main.pid"
HEARTBEAT_FILE="/tmp/heiyao_heartbeat"
HEARTBEAT_MAX_AGE=120  # 心跳超過 120 秒視為僵死

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# 單實例鎖定
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo -e "${RED}⚠️ 守護程序已在執行 (PID: $OLD_PID)${NC}"
        exit 1
    fi
    rm -f "$LOCKFILE"
fi

echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE $PIDFILE; echo '🛑 守護程序已終止'" EXIT

# 優雅關閉
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

# 清理殭屍程序
cleanup_zombies() {
    for pid in $(pgrep -f "main.py" 2>/dev/null); do
        if [ "$pid" != "$MAIN_PID" ]; then
            echo -e "${YELLOW}🧹 清理殭屍 bot: PID $pid${NC}"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
}

# 檢查心跳 + 系統健康
UNHEALTHY_COUNT=0
check_heartbeat() {
    if [ -f "$HEARTBEAT_FILE" ]; then
        local now=$(date +%s)
        local hb_time=$(stat -c %Y "$HEARTBEAT_FILE" 2>/dev/null || echo 0)
        local age=$((now - hb_time))
        if [ $age -gt $HEARTBEAT_MAX_AGE ]; then
            echo -e "${RED}💀 心跳停止 ${age}s，主程序可能僵死，強制重啟${NC}"
            return 1
        fi
        # 檢查 all_healthy 旗標
        local all_healthy=$(grep "^all_healthy=" "$HEARTBEAT_FILE" 2>/dev/null | cut -d= -f2)
        if [ "$all_healthy" = "false" ]; then
            UNHEALTHY_COUNT=$((UNHEALTHY_COUNT + 1))
            echo -e "${YELLOW}⚠️ 系統亞健康 (第 ${UNHEALTHY_COUNT} 次)${NC}"
            if [ $UNHEALTHY_COUNT -ge 3 ]; then
                echo -e "${RED}🚨 連續 3 次亞健康，強制重啟主程序${NC}"
                return 1
            fi
        else
            UNHEALTHY_COUNT=0
        fi
        echo -e "${GREEN}💓 心跳正常 (${age}s ago) 健康=${all_healthy:-?}${NC}"
        return 0
    fi
    # 剛啟動還沒心跳，給 60 秒寬限期
    local elapsed=$((SECONDS))
    if [ $elapsed -lt 60 ]; then
        echo -e "${BLUE}⏳ 等待首次心跳... (${elapsed}s)${NC}"
        return 0
    fi
    echo -e "${RED}💀 無心跳檔，強制重啟${NC}"
    return 1
}

echo ""
echo "============================================"
echo -e "${GREEN}  🤖 黑曜守護程序 v6${NC}"
echo "============================================"
echo -e "${BLUE}  啟動: $(date)${NC}"
echo -e "${BLUE}  心跳檢測: ${HEARTBEAT_MAX_AGE}s 超時${NC}"
echo -e "${GREEN}  ✅ Python: $(python3 --version)${NC}"
echo ""

# 啟動循環
RETRY=0; MAX_RETRY=50; CRASH_COUNT=0; BACKOFF=5
CRASH_WINDOW=0; CRASH_WINDOW_START=$(date +%s)

while [ $RETRY -lt $MAX_RETRY ]; do
    RETRY=$((RETRY + 1))
    SECONDS=0
    UNHEALTHY_COUNT=0
    echo -e "${GREEN}🚀 第 $RETRY 次啟動...${NC}"

    # 防打架：確保只有一個 main.py
    cleanup_zombies

    python3 main.py &
    MAIN_PID=$!
    echo $MAIN_PID > "$PIDFILE"
    echo -e "${BLUE}  PID: $MAIN_PID${NC}"

    # 等待進程結束，同時定期檢查心跳
    while kill -0 $MAIN_PID 2>/dev/null; do
        sleep 30
        if ! check_heartbeat && kill -0 $MAIN_PID 2>/dev/null; then
            echo -e "${RED}💀 心跳超時，強制終止 PID $MAIN_PID${NC}"
            kill -9 $MAIN_PID 2>/dev/null || true
            break
        fi
    done

    wait $MAIN_PID 2>/dev/null || true
    EXIT_CODE=$?

    # 智慧退避
    NOW=$(date +%s)
    WINDOW_ELAPSED=$((NOW - CRASH_WINDOW_START))
    if [ $WINDOW_ELAPSED -gt 300 ]; then
        # 超過 5 分鐘沒崩，重置計數
        CRASH_COUNT=0
        BACKOFF=5
        CRASH_WINDOW_START=$NOW
    fi
    CRASH_COUNT=$((CRASH_COUNT + 1))

    if [ $CRASH_COUNT -ge 5 ]; then
        BACKOFF=$((BACKOFF * 2))
        [ $BACKOFF -gt 300 ] && BACKOFF=300
        echo -e "${RED}⚠️ 5 分鐘內崩潰 $CRASH_COUNT 次，退避 ${BACKOFF}s${NC}"
    fi

    echo -e "${YELLOW}⚠️ 主程序終止 (Exit: $EXIT_CODE, Crash#: $CRASH_COUNT)，${BACKOFF}s 後重啟...${NC}"
    sleep $BACKOFF
done

echo -e "${RED}💀 已達最大重試次數 ($MAX_RETRY)，守護程序退出${NC}"
