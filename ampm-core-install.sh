#!/bin/bash
# 麻 Core — 一鍵安裝 30 個 AI 基礎功能
# curl -fsSL https://raw.githubusercontent.com/chainuncel0712/AMPM-AIOPS/master/ampm-core-install.sh | bash

set -e

echo "麻 Core v0.1 — 安裝中..."

# Python 3.10+ required
python3 -c "import sys; assert sys.version_info >= (3,10)" 2>/dev/null || {
    echo "需要 Python 3.10+"; exit 1
}

INSTALL_DIR="${1:-$HOME/.ampm-core}"
mkdir -p "$INSTALL_DIR"

# Download core.py
CORE_URL="https://raw.githubusercontent.com/chainuncel0712/AMPM-AIOPS/master/ampm-core-src/core.py"
echo "下載 core.py ..."
if command -v curl &>/dev/null; then
    curl -fsSL "$CORE_URL" -o "$INSTALL_DIR/core.py"
elif command -v wget &>/dev/null; then
    wget -q "$CORE_URL" -O "$INSTALL_DIR/core.py"
else
    echo "需要 curl 或 wget"
    exit 1
fi

# Test
python3 -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from core import Core
c = Core()
s = c.status()
print(f'麻 Core 完成 — {s[\"components\"]}/30 個功能就緒')
"

echo ""
echo "✅ 安裝完成"
echo "   檔案: $INSTALL_DIR/core.py"
echo "   用法:"
echo ""
echo "     import sys"
echo "     sys.path.insert(0, '$INSTALL_DIR')"
echo "     from core import Core"
echo "     c = Core()"
echo "     c.agents.create('helper', '你是一個助手')"
echo ""
