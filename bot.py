"""
AMPM Boss｜黑曜 - 獨立啟動版（安全版：從 .env 讀取 Token）
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from brain import Obsidian

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Token 從環境變數讀取 =====
TOKEN = os.getenv("TELEGRAM_TOKEN_OBSIDIAN", "")
AUTHORIZED = [int(x.strip()) for x in os.getenv("AUTHORIZED_USER_IDS", "").split(",") if x.strip()]

if not TOKEN:
    print("❌ 請設定 TELEGRAM_TOKEN_OBSIDIAN 環境變數或 .env 檔案")
    sys.exit(1)

print("🧠 啟動黑曜...")
obsidian = Obsidian()
print("✅ 就緒")

async def handle(update, context):
    uid = update.effective_user.id
    if AUTHORIZED and uid not in AUTHORIZED:
        await update.message.reply_text("⛔ 無權限")
        return
    msg = update.message.text
    logger.info(f"收到: {msg[:50]}")
    try:
        reply = obsidian.cortex.process(msg)
        await update.message.reply_text(reply[:4000])
    except Exception as e:
        await update.message.reply_text(f"⚠️ {e}")

async def start(update, context):
    await update.message.reply_text("🧠 黑曜已啟動\n/status — 健康檢查")

async def status(update, context):
    lines = ["🏥 狀態:"]
    for name in ['memory', 'tools', 'cortex']:
        o = getattr(obsidian, name, None) or obsidian.organs.get(name, None)
        if o:
            try: alive = o.is_alive()
            except: alive = True
            lines.append(f"  {'✅' if alive else '❌'} {name}")
    await update.message.reply_text("\n".join(lines))

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🤖 啟動中...")
app.run_polling()
