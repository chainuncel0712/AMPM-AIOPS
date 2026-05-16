#!/usr/bin/env python3
"""獨立 Telegram Bot 程序 — 由 main.py 啟動後 fork 出來"""
import os, sys, asyncio

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

TOKEN = os.getenv("TELEGRAM_TOKEN_OBSIDIAN", "")
AUTH_STR = os.getenv("AUTHORIZED_USER_IDS", "")
AUTHORIZED = [int(x.strip()) for x in AUTH_STR.split(",") if x.strip()]

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from brain import Obsidian

obsidian = Obsidian()

# 注入 langgraph
try:
    from core.langgraph_executor import LangGraphExecutor
    obsidian.langgraph = LangGraphExecutor(brain=obsidian)
    if hasattr(obsidian, 'cortex'):
        obsidian.cortex.langgraph = obsidian.langgraph
except Exception as e:
    print(f"[SubBot] LangGraph 啟動失敗: {e}")

# 注入器官到 obsidian
from skeleton.assembler import Assembler
assembler = Assembler()
assembler.load_link_map()
assembler.scan_and_load()
assembler.connect_all()
for name, organ in assembler.instantiated_organs.items():
    if name not in obsidian.organs:
        obsidian.organs[name] = organ

async def handle(update, context):
    msg_text = update.message.text
    print(f"[SubBot] 收到: {msg_text[:80]}", flush=True)
    if update.effective_user.id not in AUTHORIZED:
        await update.message.reply_text("⛔ 無權限")
        return
    try:
        reply = obsidian.langgraph.process(msg_text) if obsidian.langgraph else obsidian.cortex.think(msg_text)
    except Exception as e:
        reply = f"⚠️ {e}"
    print(f"[SubBot] 回覆: {reply[:80]}", flush=True)
    await update.message.reply_text(reply[:4000])

async def start_cmd(update, context):
    await update.message.reply_text("🧠 黑曜已啟動\n/status — 健康檢查")

async def status_cmd(update, context):
    lines = ["🏥 狀態:"]
    lines.append(f"📊 零件: {len(obsidian.organs)}")
    lines.append(f"🔗 langgraph: {'✅' if obsidian.langgraph else '❌'}")
    await update.message.reply_text("\n".join(lines))

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("[SubBot] 已啟動", flush=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
