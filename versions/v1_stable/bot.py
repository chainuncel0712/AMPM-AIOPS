#!/usr/bin/env python3
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config
from brain import Obsidian

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🧠 啟動黑曜...")
obsidian = Obsidian()
print("✅ 就緒")

async def handle(update, context):
    msg = update.message.text
    logger.info(f"收到: {msg[:50]}")
    
    def send_func(text):
        pass
    
    try:
        reply = obsidian.process_message(msg, send_func)
        await update.message.reply_text(reply[:4000])
    except Exception as e:
        await update.message.reply_text(f"錯誤: {e}")

async def start(update, context):
    await update.message.reply_text("🧠 黑曜已啟動")

app = Application.builder().token(config.telegram_token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🤖 啟動中...")
app.run_polling()
