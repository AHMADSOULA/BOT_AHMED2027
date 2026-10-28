import asyncio
import os
from aiohttp import web
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import config
from bot import handlers
from database.db import init_db
from utils.logger import get_logger
from utils.helpers import extract_urls

log = get_logger("Main")

async def post_init(app):
    # ✅ نستناو init_db تكمل 100%
    await init_db()
    log.info("✅ DB ready")

    from database import db
    await db.register_user(config.ADMIN_ID, "ADMIN")
    log.info("✅ ADMIN registered")

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

async def main():
    log.info("🚀 starting...")

    # ✅ نجهزو البوت
    app = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("status", handlers.status_cmd))
    app.add_handler(CommandHandler("cancel", handlers.cancel_cmd))
    app.add_handler(CommandHandler("request", handlers.request_cmd))
    app.add_handler(CallbackQueryHandler(handlers.button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    # ✅ نجهزو HTTP Server
    port = int(os.getenv("PORT", 8080))
    web_app = web.Application()
    web_app.router.add_get("/", health_check)
    web_app.router.add_get("/health", health_check)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"✅ HTTP Server على port {port}")

    # ✅ نشغلو البوت
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    log.info("🚀 البوت شغال!")
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
