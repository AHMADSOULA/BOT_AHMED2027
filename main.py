
import os
import asyncio

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import config
from bot import handlers
from database.db import init_db
from utils.logger import get_logger

log = get_logger("Main")


async def post_init(app: Application):
    """تهيئة قاعدة البيانات عند تشغيل البوت."""
    await init_db()
    log.info("✅ DB ready")


async def route_text(update, context):
    """توجيه الرسائل النصية والروابط."""
    if not update.message or not update.message.text:
        return

    from utils.helpers import extract_urls

    message_text = update.message.text.strip()

    if extract_urls(message_text):
        await handlers.handle_url(update, context)
        return

    await update.message.reply_text(
        "ℹ️ أرسل /start للبدء، أو أرسل رابط Google Skills."
    )


async def error_handler(update, context):
    """تسجيل الأخطاء بدل توقف البوت بسبب خطأ في تحديث واحد."""
    log.error(
        "حدث خطأ أثناء معالجة تحديث Telegram",
        exc_info=(
            type(context.error),
            context.error,
            context.error.__traceback__,
        ) if context.error else None,
    )


def main():
    """تشغيل بوت Telegram."""
    if not config.BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود. أضفه في Environment Variables على Render."
        )

    log.info("🚀 starting...")

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # أوامر البوت الموجودة فعلًا في bot/handlers.py
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("status", handlers.status_cmd))
    app.add_handler(CommandHandler("cancel", handlers.cancel_cmd))

    # أزرار القائمة
    app.add_handler(
        CallbackQueryHandler(handlers.button_handler)
    )

    # استقبال الروابط والرسائل النصية
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            route_text,
        )
    )

    # تسجيل الأخطاء
    app.add_error_handler(error_handler)

    log.info("✅ Telegram handlers registered")
    log.info("🤖 Bot is starting polling...")

    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
