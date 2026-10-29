"""
automation/sso_flow.py
- رسالة وحدة كتبدل مع الخطوات
- سريع وما كياكلش الرام بزاف
- كيكتشف إلا رجع لصفحة تسجيل الدخول (Sign in) وكيرجع account_deleted
"""
import re
import asyncio
from urllib.parse import urlparse, parse_qs

from automation.console import CloudConsole
from utils.logger import get_logger

log = get_logger("SSOFlow")


def extract_project_id(url: str) -> str:
    m = re.search(r'(qwiklabs-gcp-[\w-]+)', url or "")
    return m.group(1) if m else None


def extract_domain_from_service_url(service_url: str) -> str:
    s = (service_url or "").strip()
    if s.startswith("http://") or s.startswith("https://"):
        return urlparse(s).netloc.strip()
    return s.replace("http://", "").replace("https://", "").split("/")[0].strip()


def extract_authuser(page_url: str) -> str:
    try:
        qs = parse_qs(urlparse(page_url).query)
        return qs.get('authuser', ['1'])[0]
    except Exception:
        return '1'


def extract_email_from_url(url: str) -> str:
    try:
        m = re.search(r'Email%3D([^%&]+%40qwiklabs\.net)', url or "")
        if m:
            from urllib.parse import unquote
            return unquote(m.group(1))
        m = re.search(r'Email=([^&\s#]+@qwiklabs\.net)', url or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _has_password(url: str) -> bool:
    return "password=" in (url or "").lower()


async def _is_dashboard(page) -> bool:
    try:
        return await page.evaluate("""
            () => {
                const url = window.location.href.toLowerCase();
                if (url.includes('console.cloud.google.com') &&
                    !url.includes('signin') &&
                    !url.includes('accounts.google.com')) {
                    const body = (document.body.innerText || '').toLowerCase();
                    if (body.includes('sign in') && body.includes('google account')) return false;
                    return true;
                }
                return false;
            }
        """)
    except Exception:
        return False


async def _is_blocked(page) -> str:
    """Return account_deleted only for explicit deletion/closure messages."""
    try:
        return await page.evaluate("""
            () => {
                const body = (document.body.innerText || '').toLowerCase();
                const explicit = [
                    'account deleted', 'account has been deleted', 'account is closed',
                    'your account has been deleted', 'تم حذف الحساب', 'تم إغلاق الحساب'
                ];
                return explicit.some(t => body.includes(t)) ? 'account_deleted' : null;
            }
        """)
    except Exception:
        return None


async def run_sso_flow(context, sso_url: str, image: str, sender=None, user_tag="@user") -> dict:
    project_id = extract_project_id(sso_url)
    if not project_id:
        raise RuntimeError("❌ Project ID ماكانش في الرابط.")

    if _has_password(sso_url):
        region = "us-central1"
        flag = "🇺🇸"
    else:
        region = "europe-west1"
        flag = "🇧🇪"

    log.info(f"🚀 SSO — project={project_id}")
    console = CloudConsole(context, sender=sender, user_tag=user_tag)

    page = await context.new_page()
    try:
        # 1
        if sender:
            try: await sender.edit_text("⏳ جاري التنفيذ... [1/6] فتح الرابط")
            except: pass
            
        try:
            await page.goto(sso_url, wait_until="domcontentloaded", timeout=40000)
        except Exception:
            await page.goto(sso_url, wait_until="commit", timeout=40000)

        await page.wait_for_timeout(1500)
        await console._shot(page, "📸 الخطوة 1/7: فتح رابط الجلسة")

        blocked = await _is_blocked(page)
        if blocked:
            await page.screenshot(path="/tmp/blocked.png")
            return {"success": False, "error": blocked, "message": "❌ حساب محذوف أو مغلق", "screenshot": "/tmp/blocked.png"}

        # 2
        if sender:
            try: await sender.edit_text("⏳ جاري التنفيذ... [2/6] شروط الخدمة TOS")
            except: pass
            
        try:
            await console.step1_welcome_screen(page)
        except Exception as e:
            log.warning(f"step1 welcome failed: {e}")
        await console._shot(page, "📸 الخطوة 2/7: صفحة Welcome بعد النزول والمتابعة")
        await page.wait_for_timeout(1000)

        # 3
        if sender:
            try: await sender.edit_text("⏳ جاري التنفيذ... [3/6] الموافقة Terms")
            except: pass
            
        try:
            await console.step2_terms_dialog(page)
        except Exception as e:
            log.warning(f"step2 terms failed: {e}")
        await console._shot(page, "📸 الخطوة 3/7: فحص صفحة الموافقة")
        await page.wait_for_timeout(1000)

        # 4
        if sender:
            try: await sender.edit_text("⏳ جاري التنفيذ... [4/6] انتظار Dashboard")
            except: pass

        dashboard_ok = False
        for i in range(60): # انتظر حتى دقيقة لانتقال الصفحة
            await page.wait_for_timeout(1000)
            blocked = await _is_blocked(page)
            if blocked:
                await page.screenshot(path="/tmp/blocked.png")
                return {"success": False, "error": blocked, "message": "❌ حساب محذوف أو مغلق", "screenshot": "/tmp/blocked.png"}

            if await _is_dashboard(page):
                dashboard_ok = True
                break

        if not dashboard_ok:
            shot = "/tmp/blocked.png"
            try:
                await page.screenshot(path=shot, timeout=15000, animations="disabled")
            except Exception as e:
                log.warning(f"final screenshot failed: {e}")
                shot = None
            return {"success": False, "error": "signin_or_consent_pending", "message": "❌ لم نصل إلى Dashboard. قد تحتاج صفحة تسجيل الدخول أو الموافقة إلى تدخل يدوي؛ هذا لا يعني أن الحساب محذوف.", "screenshot": shot}

        authuser = extract_authuser(page.url)

        # 5
        if sender:
            try: await sender.edit_text("⏳ جاري التنفيذ... [5/6] تفعيل API")
            except: pass
            
        try:
            await console.step3_enable_api(page, project_id, authuser)
        except Exception as e:
            log.warning(f"step3 API failed: {e}")
        await console._shot(page, "📸 الخطوة 4/7: صفحة تفعيل Cloud Run API")

        # 6
        if sender:
            try: await sender.edit_text("⏳ جاري التنفيذ... [6/6] إنشاء Cloud Run")
            except: pass
            
        await console._shot(page, "📸 الخطوة 5/7: قبل إعداد خدمة Cloud Run")
        try:
            await console.step4_create_cloud_run(page, project_id, authuser, image, region=region)
            await console._shot(page, "📸 الخطوة 6/7: تم إرسال طلب إنشاء الخدمة")
        except Exception as e:
            shot = "/tmp/blocked.png"
            try: await page.screenshot(path=shot, timeout=15000, animations="disabled")
            except Exception: shot = None
            return {"success": False, "error": "step4_failed", "message": str(e)[:200], "screenshot": shot}

        await page.wait_for_timeout(500)

        # 7 - انتظار الرابط
        try:
            final_url = await console.step5_get_deployed_url(page)
            domain = extract_domain_from_service_url(final_url)
        except Exception as e:
            shot = "/tmp/blocked.png"
            try: await page.screenshot(path=shot, timeout=15000, animations="disabled")
            except Exception: shot = None
            return {"success": False, "error": "step5_failed", "message": str(e)[:200], "screenshot": shot}

    finally:
        try: await page.close()
        except: pass

    return {
        "success": True,
        "final_url": final_url,
        "domain": domain,
        "flag": flag,
    }
