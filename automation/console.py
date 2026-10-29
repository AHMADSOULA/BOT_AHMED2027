"""
automation/console.py
كل خطوات Google Cloud Console — بلا تصوير عادي
"""
import asyncio
from playwright.async_api import expect
from utils.logger import get_logger

log = get_logger("Console")


class CloudConsole:
    def __init__(self, context, sender=None, user_tag=None):
        self.context = context
        self.sender = sender
        self.user_tag = user_tag or "@user"

    async def _shot(self, page, caption: str = ""):
        """screenshot + send (غير عند الفشل)"""
        if not self.sender:
            return
        try:
            path = f"/tmp/shot_{int(asyncio.get_event_loop().time()*1000)}.png"
            await page.screenshot(path=path, full_page=False, timeout=8000)
            with open(path, "rb") as f:
                try:
                    await self.sender.reply_photo(photo=f, caption=caption[:1000])
                    log.info(f"📸 {caption}")
                except Exception as e:
                    log.warning(f"⚠️ reply_photo: {e}")
            import os
            try:
                os.remove(path)
            except Exception:
                pass
        except Exception as e:
            log.warning(f"⚠️ _shot: {e}")

    # ═══════════════════════════════════════
    # STEP 1
    # ═══════════════════════════════════════

    async def _click_visible_action(self, page, labels, step_name):
        """Click a real, visible and enabled Google consent/continue control.

        Google changes button markup and sometimes nests the consent UI in a
        frame, so inspect all current frames and several accessible/text selectors.
        Never force-enable a consent control.
        """
        selectors = []
        for label in labels:
            selectors.extend([
                ("role", label),
                ("text", label),
            ])

        # Re-read frames on each attempt because Google may add a frame late.
        for _ in range(4):
            for frame in list(page.frames):
                for kind, label in selectors:
                    try:
                        if kind == "role":
                            loc = frame.get_by_role("button", name=label, exact=False).first
                        else:
                            loc = frame.get_by_text(label, exact=True).first
                        if await loc.is_visible(timeout=500):
                            try:
                                enabled = await loc.is_enabled()
                            except Exception:
                                enabled = True
                            if enabled:
                                await loc.click(timeout=2500)
                                log.info(f"✅ {step_name}: clicked visible control '{label}'")
                                await page.wait_for_timeout(1200)
                                return True
                    except Exception:
                        continue
            await page.wait_for_timeout(700)
        return False

    async def step1_welcome_screen(self, page):
        """Handle the Google Welcome screen if a normal continuation control exists."""
        log.info("🚀 step1 — Welcome")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=12000)
        except Exception:
            pass
        await page.wait_for_timeout(1200)
        labels = ["I understand", "Got it", "Continue", "Next"]
        if not await self._click_visible_action(page, labels, "Welcome"):
            log.info("ℹ️ No visible enabled Welcome action; leaving page for review")

    async def step2_terms_dialog(self, page):
        """Handle visible consent buttons; if consent is unavailable, report it clearly."""
        log.info("🚀 step2 — terms/consent")
        labels = ["I understand", "Agree and continue", "Accept", "Agree", "Continue"]
        if not await self._click_visible_action(page, labels, "Terms"):
            log.warning("⚠️ Consent action not found/enabled. Manual review may be required.")

    # ═══════════════════════════════════════
    # STEP 3
    # ═══════════════════════════════════════

    async def step3_enable_api(self, page, project_id, authuser):
        log.info("🚀 step3")

        api_url = (
            f"https://console.cloud.google.com/apis/library/"
            f"run.googleapis.com?project={project_id}&authuser={authuser}"
        )
        await page.goto(api_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        try:
            if "accounts.google.com" in page.url.lower():
                log.warning("⚠️ sign in — نتجاوزو")
                return
        except Exception:
            pass

        enable_btn = page.get_by_role("button", name="Enable")
        manage_btn = page.get_by_role("button", name="Manage")
        disable_btn = page.get_by_text("Disable API")

        try:
            await expect(enable_btn.or_(manage_btn)).to_be_visible(timeout=10000)
            if await enable_btn.is_visible():
                await enable_btn.click()
                try:
                    await expect(manage_btn.or_(disable_btn)).to_be_visible(timeout=45000)
                except Exception:
                    pass
            elif await manage_btn.is_visible():
                log.info("ℹ️ API مفعّل")
        except Exception as e:
            log.warning(f"⚠️ step3: {e}")

    # ═══════════════════════════════════════
    # STEP 4 — مع region
    # ═══════════════════════════════════════

    async def step4_create_cloud_run(self, page, project_id, authuser, image, region="us-central1"):
        run_url = (
            f"https://console.cloud.google.com/run/create"
            f"?project={project_id}&authuser={authuser}&region={region}"
        )
        log.info(f"🌐 step4 — region={region}")

        await page.goto(run_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        image_found = False
        try:
            label = page.get_by_text("Container Image URL").first
            await label.click(timeout=10000)
            image_found = True
        except Exception:
            try:
                clicked = await page.evaluate("""
                    () => {
                        for (const el of document.querySelectorAll('*')) {
                            const t = (el.innerText || '').trim();
                            if (t.includes('Container Image URL') && t.length < 100) {
                                try { el.click(); return 'ok'; } catch (e) {}
                            }
                        }
                        return null;
                    }
                """)
                if clicked:
                    image_found = True
            except Exception:
                pass

        if not image_found:
            try:
                inp = page.locator('input[type="text"]').first
                await inp.click(timeout=5000)
            except Exception as e:
                raise RuntimeError(f"فشل حقل: {e}")

        await page.wait_for_timeout(500)
        await page.keyboard.type(image, delay=30)

        await page.wait_for_timeout(2000)

        try:
            await page.get_by_role("radio", name="Allow public access").click(timeout=8000)
        except Exception:
            pass
        try:
            await page.get_by_role("radio", name="Instance-based").click(timeout=8000)
        except Exception:
            pass
        try:
            await page.get_by_role("button", name="Hide").click(timeout=1500)
        except Exception:
            pass

        await page.keyboard.press("End")
        await page.wait_for_timeout(800)

        try:
            create_btn = page.get_by_role("button", name="Create")
            await create_btn.click(force=True, timeout=8000)
            log.info("✅ Create")
        except Exception as e:
            try:
                clicked = await page.evaluate("""
                    () => {
                        for (const el of document.querySelectorAll('button, [role="button"]')) {
                            if (el.offsetParent === null || el.disabled) continue;
                            const t = (el.innerText || '').trim().toLowerCase();
                            if (t === 'create' || t === 'deploy') {
                                try { el.click(); return t; } catch (e) {}
                            }
                        }
                        return null;
                    }
                """)
                if not clicked:
                    raise RuntimeError(f"فشل Create: {e}")
            except Exception as e2:
                raise RuntimeError(f"فشل Create: {e2}")

    # ═══════════════════════════════════════
    # STEP 5
    # ═══════════════════════════════════════

    async def step5_get_deployed_url(self, page):
        log.info("⏳ step5")

        link_locator = page.locator('a[href*="run.app"]')
        try:
            await link_locator.wait_for(state="visible", timeout=60000)
            final_url = await link_locator.get_attribute("href")
            return final_url
        except Exception:
            pass

        for i in range(30):
            try:
                url = await page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('a');
                        for (const a of links) {
                            const href = a.href || '';
                            if (href.includes('.run.app')) return href.split('?')[0].split('#')[0];
                        }
                        const body = document.body.innerText || '';
                        const m = body.match(/https:\\/\\/[a-zA-Z0-9\\-]+\\.run\\.app/);
                        if (m) return m[0];
                        return null;
                    }
                """)
                if url:
                    return url
            except Exception:
                pass
            await page.wait_for_timeout(3000)

        raise RuntimeError("ما لقيناش رابط run.app")
