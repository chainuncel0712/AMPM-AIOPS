#!/bin/bash
echo "=========================================="
echo "🤖 AMPM Bot 自動管理"
echo "=========================================="

cd ~/AMPM_Brain

python3 << 'PYTHON_SCRIPT'
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

env_path = Path.home() / "AMPM_Brain" / ".env"
load_dotenv(dotenv_path=env_path)

print("\n📋 當前 .env 中的所有 Telegram Bot：")
print("-" * 60)

bot_count = 0
for key, value in os.environ.items():
    if key.startswith("TELEGRAM_TOKEN_"):
        bot_count += 1
        try:
            url = f"https://api.telegram.org/bot{value}/getMe"
            r = requests.get(url, timeout=5)
            if r.ok and r.json().get("ok"):
                bot = r.json()["result"]
                print(f"✅ {key}")
                print(f"   → @{bot['username']} (ID: {bot['id']})")
                print(f"   → 名稱: {bot['first_name']}")
            else:
                print(f"⚠️ {key}: Token 無效")
        except Exception as e:
            print(f"❌ {key}: 無法連線 - {e}")
        print()

if bot_count == 0:
    print("⚠️ 沒有找到任何 TELEGRAM_TOKEN_ 開頭的設定")
    print("\n📝 新增 Bot 的方式：")
    print("   在 .env 中加入一行：")
    print("   TELEGRAM_TOKEN_你的名稱=你的Token")
else:
    print("-" * 60)
    print(f"📊 總共 {bot_count} 個 Bot")

print("\n" + "=" * 60)
PYTHON_SCRIPT
