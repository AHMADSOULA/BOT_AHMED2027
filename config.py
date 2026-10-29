
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env إن وُجد
load_dotenv()


class Config:
    # توكن بوت Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

    # رقم حساب المدير
    ADMIN_ID = int(os.getenv("ADMIN_ID", "7119011124").strip())

    # تشغيل المتصفح بدون واجهة رسومية
    HEADLESS = os.getenv("HEADLESS", "true").strip().lower() in (
        "true", "1", "yes", "on"
    )

    # صورة Docker الافتراضية للنشر على Cloud Run
    DEFAULT_IMAGE = os.getenv(
        "DEFAULT_IMAGE",
        "docker.io/ajndjd2/ahmed-vip1"
    ).strip()


# إنشاء كائن الإعدادات الذي يستعمله المشروع
config = Config()
