FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV HEADLESS=true
ENV PORT=8080

WORKDIR /app

# ✅ ننسخو requirements أولاً (للكاشينغ)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ نثبتو المتصفح
RUN playwright install chromium
RUN playwright install-deps chromium

# ✅ ننسخو باقي الملفات
COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
