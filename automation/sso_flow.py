import re
from automation.console import CloudConsole
from utils.logger import get_logger

log = get_logger("SSOFlow")

def extract_project_id(url: str) -> str:
    m = re.search(r'(qwiklabs-gcp-[\w-]+)', url or "")
    return m.group(1) if m else None

async def run_sso_flow(context, sso_url: str, image: str, sender=None, user_tag="@user") -> dict:
    project_id = extract_project_id(sso_url)
    if not project_id:
        return {"success": False, "message": "❌ Project ID ماكانش في الرابط."}

    console = CloudConsole(context, sender=None, user_tag=user_tag)
    page = await context.new_page()
    try:
        await page.goto(sso_url, wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(1500)
        
        # ... (هنا كاين الكود اللي كيدير الخطوات step1, step2, step3, step4)
        # ... (إلا بغيتي الكود ديال console.py كامل قولها ليا)

        # مثال للنتيجة:
        return {
            "success": True,
            "final_url": "https://example.run.app",
            "domain": "example.run.app",
            "flag": "🇺🇸"
        }
    except Exception as e:
        await page.screenshot(path="/tmp/blocked.png")
        return {"success": False, "message": str(e)[:200], "screenshot": "/tmp/blocked.png"}
    finally:
        await page.close()
