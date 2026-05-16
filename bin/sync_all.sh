#!/bin/bash
echo "=========================================="
echo "🔄 AMPM 一鍵同步"
echo "=========================================="

cd ~/AMPM_Brain

echo ""
echo "📡 同步 Telegram Bot 資訊..."

python3 << 'PYTHON_SCRIPT'
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(".env")
load_dotenv(dotenv_path=env_path)

print("\n✅ 有效 Token：")
valid_count = 0
for key, value in os.environ.items():
    if key.startswith("TELEGRAM_TOKEN_"):
        try:
            url = f"https://api.telegram.org/bot{value}/getMe"
            r = requests.get(url, timeout=5)
            if r.ok and r.json().get("ok"):
                bot = r.json()["result"]
                print(f"   ✅ @{bot['username']} ({key})")
                valid_count += 1
            else:
                print(f"   ❌ {key}: Token 無效")
        except:
            print(f"   ❌ {key}: 連線失敗")

print(f"\n📊 統計：有效 {valid_count} 個")

# 儲存快取
cache_file = Path.home() / ".ampm_brain" / "data" / "telegram_bots_cache.json"
cache_file.parent.mkdir(parents=True, exist_ok=True)
cache_file.write_text("同步完成於 $(date)")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ 同步完成"
echo "=========================================="
