# بوت نشر Cloud Run — إعداد Render

## الملفات
- `main.py`: تشغيل بوت تيليجرام.
- `config.py`: قراءة إعدادات البيئة.
- `bot/`: أوامر البوت والأزرار.
- `automation/`: أتمتة المتصفح وواجهة Cloud Run.
- `database/`: قاعدة بيانات SQLite.
- `Dockerfile`: صورة Playwright مع Chromium ومكتبات النظام.
- `render.yaml`: تعريف خدمة Background Worker على Render.
- `requirements.txt`: مكتبات Python.

## النشر
1. ارفع محتويات هذا المجلد إلى مستودع GitHub جديد أو حدّث المستودع الذي تستخدمه.
2. في Render اختر **New + → Blueprint** واربط المستودع الذي يحتوي `render.yaml`، أو أنشئ **Background Worker** يدويًا باستخدام Dockerfile.
3. أضف متغير البيئة `BOT_TOKEN` في Render وضع توكن بوت تيليجرام. لا تضع التوكن في GitHub ولا تشاركه.
4. ابدأ النشر وانتظر اكتمال بناء Docker. هذه الصورة تثبّت Chromium داخل `/ms-playwright` لتفادي خطأ `Executable doesn't exist`.

## إعدادات الخدمة
- Build: Dockerfile (لا تستخدم أمر pip الخاص بـ Native Runtime).
- Start command: يحدده Dockerfile (`python main.py`).
- نوع الخدمة: Background Worker لأن البوت يستخدم Telegram polling ولا يحتاج منفذ HTTP.
- صورة Cloud Run الافتراضية: `docker.io/ajndjd2/ahmed-vip1`.

## تنبيهات
- قاعدة البيانات والمتصفح داخل `/tmp` مؤقتان وقد يختفيان عند إعادة التشغيل أو إعادة النشر.
- إذا ظهرت مشكلة في Chromium، تأكد أن Render يبني المشروع باستخدام Dockerfile وليس Native Python Runtime.
- أكمل أي تحقق أمني أو CAPTCHA يدويًا عند ظهوره؛ لا تعتمد على تجاوز آليات الحماية.


## مهم في Render
هذا البوت يستخدم Telegram polling ولا يفتح HTTP port؛ شغّله كـ **Background Worker** وليس Web Service. إذا كان عندك Web Service موجود مسبقًا، تغيير `render.yaml` وحده لا يغيّر نوع الخدمة الموجودة تلقائيًا: أنشئ Background Worker من نفس المستودع أو غيّر إعداد الخدمة يدويًا إن أتاح Render ذلك.

إذا ظهرت صفحة موافقة Google أو تسجيل دخول، أكملها بالطريقة العادية يدويًا. البوت لا يتجاوز CAPTCHA ولا يفرض تفعيل أزرار الموافقة.
