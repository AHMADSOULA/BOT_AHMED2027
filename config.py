
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

    ADMIN_ID = int(os.getenv("ADMIN_ID", "7119011124").strip())

    HEADLESS = os.getenv("HEADLESS", "true").strip().lower() in (
        "true", "1", "yes", "on"
    )

    DEFAULT_IMAGE = os.getenv(
        "DEFAULT_IMAGE",
        "docker.io/ajndjd2/ahmed-vip1"
    ).strip()

    # مسار قاعدة بيانات المستخدمين
    DB_PATH = os.getenv("DB_PATH", "/app/data/bot.db").strip()


config = Config()
