الملفات المعدلة فقط

1) استبدل config.py الموجود عندك بهذا الملف. أضيف ADMIN_ID حتى لا يظهر AttributeError عند قراءة config.ADMIN_ID.
2) render.yaml يضيف ADMIN_ID كمتغير بيئة في Render Blueprint.
3) في Render > Environment أضف ADMIN_ID وضع رقم حساب المدير فقط، بدون علامات اقتباس.

حل Conflict getUpdates: هذا ليس خطأ في config.py. أوقف كل النسخ الأخرى التي تستخدم نفس BOT_TOKEN (Render/Railway/Pydroid/أي استضافة) وشغّل نسخة واحدة فقط. لا تشغّل نسختين polling بنفس التوكن.

ملاحظة: render.yaml يفترض أن مشروعك يستخدم Dockerfile في جذر المستودع.
