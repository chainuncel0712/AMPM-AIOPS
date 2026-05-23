#!/usr/bin/env python3
"""AMPM Service Bot — 售後服務客服機器人（獨立執行）"""

import os, sys, json, logging
from pathlib import Path

SRC_PATH = str(Path(__file__).parent / "src")
if SRC_PATH in sys.path:
    sys.path.remove(SRC_PATH)
sys.path.insert(0, SRC_PATH)

import support
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

TOKEN = os.getenv("TELEGRAM_TOKEN_SERVICE", "")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Service] %(message)s")
logging.info(f"TOKEN loaded: len={len(TOKEN)}")
if not TOKEN:
    logging.error("TELEGRAM_TOKEN_SERVICE is empty!")
    sys.exit(1)


async def start(update: Update, context):
    await update.message.reply_text(
        "👋 歡迎來到黑曜售後服務！\n"
        "請問有什麼問題？輸入關鍵字如「部署」「付款」「授權」我就能回答。\n"
        "解決不了會請管理員接手。"
    )


async def handle(update: Update, context):
    msg = update.message.text
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"from @{user.username or user.id} in {chat.type}: {msg[:60]}")

    # 先查 FAQ
    reply = support.find_answer(msg)
    if reply:
        await update.message.reply_text(reply)
        return

    # 群組裡沒匹配到，提示管理員
    if chat.type in ("group", "supergroup"):
        await update.message.reply_text(
            "🤔 這個問題我暫時無法回答，稍後管理員會來處理。"
        )
    else:
        await update.message.reply_text(
            "🤔 我不太確定你的問題，試試關鍵字：部署、付款、授權、功能、錯誤"
        )


def main():
    while True:
        try:
            app = Application.builder().token(TOKEN).build()
            app.add_handler(CommandHandler("start", start))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
            logging.info("Service Bot started, polling...")
            app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logging.error(f"Bot crashed: {e}, restarting in 10s...")
            import time
            time.sleep(10)


if __name__ == "__main__":
    main()
