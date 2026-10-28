import asyncio
import os
import threading
from aiohttp import web
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import config
from bot import handlers
from database.db import init_db
from utils.logger import get_logger
from utils.helpers import extract_urls

log = get_logger("Main")


async def route_text(update, context):
    from database import db
    user = update.effective_user
    text = update.message.text or ""

    if await handlers.handle_admin_input(update, context, text):
        return

    if extract_urls(text):
        await handlers.handle_url(update, context)
        return

    session = await db.get_session(user.id)
    if session and session.get("state") == "waiting_password":
        await handlers.handle_password(update, context)
        return

    await update.message.reply_text("ℹ️ أرسل /start للبدء.")


async def health_check(request):
    return web.Response(text="OK")


def run_http_server():
    """HTTP Server فـ thread منفصل باش Render يلقى port"""
    port = int(os.getenv("PORT", 8080))
    web_app = web.Application()
    web_app.router.add_get("/", health_check)
    web_app.router.add_get("/health", health_check)

    log.info(f"✅ HTTP Server على port {port}")
    web.run_app(web_app, host="0.0.0.0", port=port, print=None)


def main():
    log.info("🚀 starting...")

    # ✅ 1. نخلقو الجداول أولاً
    asyncio.run(init_db())
    log.info("✅ DB ready")

    # ✅ 2. نسجلو الأدمن
    async def _register():
        from database import db
        await db.register_user(config.ADMIN_ID, "ADMIN")
    asyncio.run(_register())
    log.info("✅ ADMIN registered")

    # ✅ 3. نشغلو HTTP Server فـ thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # ✅ 4. نجهزو البوت
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("status", handlers.status_cmd))
    app.add_handler(CommandHandler("cancel", handlers.cancel_cmd))
    app.add_handler(CommandHandler("request", handlers.request_cmd))
    app.add_handler(CallbackQueryHandler(handlers.button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    log.info("🚀 البوت شغال!")

    # ✅ 5. نشغلو البوت (بلا asyncio.run)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
