#!/bin/bash
# 麻 Core — 一鍵安裝 30 個 AI 基礎功能
# curl -fsSL https://...../install.sh | bash

set -e

echo "麻 Core v0.1 — 安裝中..."

# Python 3.10+ required
python3 -c "import sys; assert sys.version_info >= (3,10)" 2>/dev/null || {
    echo "需要 Python 3.10+"; exit 1
}

# Install dir
INSTALL_DIR="${1:-$HOME/.ampm-core}"
mkdir -p "$INSTALL_DIR"

# Core file
CORE_URL="https://raw.githubusercontent.com/AMPM-AI/ampm-core/main/src/core.py"
if command -v curl &>/dev/null; then
    curl -fsSL "$CORE_URL" -o "$INSTALL_DIR/core.py" 2>/dev/null || {
        echo "⚠️  無法從 GitHub 下載，使用本地副本"
        cp "$(dirname "$0")/src/core.py" "$INSTALL_DIR/core.py" 2>/dev/null
    }
else
    cp "$(dirname "$0")/src/core.py" "$INSTALL_DIR/core.py" 2>/dev/null
fi

# Quick test
python3 -c "
import sys; sys.path.insert(0, '$INSTALL_DIR')
from core import Core
c = Core()
s = c.status()
print(f'麻 Core 安裝成功 — {s[\"components\"]} 個功能就緒')
print(f'版本: {s[\"version\"]}')
" || {
    echo "❌ 安裝驗證失敗"
    exit 1
}

echo ""
echo "✅ 麻 Core 安裝完成"
echo "   位置: $INSTALL_DIR/core.py"
echo "   用法:"
echo "     from core import Core"
echo "     c = Core()"
echo "     c.agents.create('helper', '你是一個助手')"
echo ""
