"""
AMPM Boss｜黑曜 - 不再獨立啟動
================================
此檔案不再作為獨立入口。
請使用 python main.py 啟動整個系統。

提供 start_bot() 函數供 main.py 呼叫。
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from telegram.ext import Application, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN_OBSIDIAN", "")
AUTHORIZED = [int(x.strip()) for x in os.getenv("AUTHORIZED_USER_IDS", "").split(",") if x.strip()]


def start_bot(obsidian) -> Application:
    """由 main.py 呼叫啟動 Telegram Bot。不回傳就不啟動。"""
    from governance.gatekeeper import gatekeeper
    gatekeeper.check_module_permission("bot", "start")

    if not TOKEN:
        print("⚠️ [Bot] 未設定 TELEGRAM_TOKEN_OBSIDIAN，不啟動 Telegram Bot")
        return None

    application = Application.builder().token(TOKEN).build()

    from bot_handler import (
        start, help_command, status_command, handle_message,
        mode_command, switch_model, upgrade_command, list_models,
        handle_callback
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("mode", mode_command))
    application.add_handler(CommandHandler("model", switch_model))
    application.add_handler(CommandHandler("upgrade", upgrade_command))
    application.add_handler(CommandHandler("models", list_models))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CallbackQuery, handle_callback))

    application.bot_data["obsidian"] = obsidian
    application.bot_data["authorized"] = AUTHORIZED

    return application


if __name__ == "__main__":
    print("❌ bot.py 不再作為獨立入口。請執行: python main.py")
    sys.exit(1)
