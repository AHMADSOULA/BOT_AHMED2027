import os
from playwright.async_api import async_playwright
from config import config
from automation.stealth import STEALTH_JS
from utils.logger import get_logger

log = get_logger("Browser")

class StealthBrowser:
    def __init__(self):
        self.playwright = None
        self.context = None

    async def start(self):
        self.playwright = await async_playwright().start()
        os.makedirs(config.CHROME_PROFILE_DIR, exist_ok=True)
        args = [
            "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled", "--disable-gpu"
        ]
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=config.CHROME_PROFILE_DIR,
            headless=config.HEADLESS,
            args=args,
            viewport={"width": 1280, "height": 720},
            user_agent=config.USER_AGENT,
        )
        await self.context.add_init_script(STEALTH_JS)
        self.context.set_default_timeout(config.PAGE_TIMEOUT)
        self.context.set_default_navigation_timeout(config.NAV_TIMEOUT)
        log.info("✅ المتصفح جاهز")
        return self.context

    async def close(self):
        if self.context:
            try: await self.context.close()
            except: pass
        if self.playwright:
            try: await self.playwright.stop()
            except: pass
