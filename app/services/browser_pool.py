import asyncio
import logging
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright
from app.config import settings

logger = logging.getLogger(__name__)


class BrowserPool:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browsers: List[Browser] = []
        self._semaphore = asyncio.Semaphore(settings.BROWSER_POOL_SIZE)
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        logger.info(f"Initializing browser pool with size {settings.BROWSER_POOL_SIZE}")
        self.playwright = await async_playwright().start()

        for i in range(settings.BROWSER_POOL_SIZE):
            await self._launch_browser()

        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def _launch_browser(self):
        browser = await self.playwright.chromium.launch(
            headless=settings.BROWSER_HEADLESS,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        self.browsers.append(browser)
        logger.info(f"Launched browser instance (Total: {len(self.browsers)})")

    async def stop(self):
        logger.info("Closing browser pool...")
        if self._monitor_task:
            self._monitor_task.cancel()

        for browser in self.browsers:
            await browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser pool closed.")

    async def acquire_context(self) -> BrowserContext:
        async with self._semaphore:
            healthy_browsers = [b for b in self.browsers if b.is_connected()]
            if not healthy_browsers:
                logger.warning("No healthy browsers found, relaunching...")
                await self._launch_browser()
                browser = self.browsers[-1]
            else:
                browser = healthy_browsers[0]

            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            context.set_default_timeout(settings.BROWSER_TIMEOUT_MS)
            return context

    async def release_context(self, context: BrowserContext):
        try:
            await context.close()
        except Exception as e:
            logger.error(f"Error releasing browser context: {e}")

    async def _monitor_loop(self):
        while True:
            try:
                await asyncio.sleep(30)

                for i, browser in enumerate(self.browsers):
                    if not browser.is_connected():
                        logger.warning(f"Browser {i} disconnected, restarting...")
                        await self._restart_browser(i)
                        continue

                    pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in browser monitor loop: {e}")

    async def _restart_browser(self, index: int):
        try:
            await self.browsers[index].close()
        except Exception:
            pass

        browser = await self.playwright.chromium.launch(
            headless=settings.BROWSER_HEADLESS,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        self.browsers[index] = browser
        logger.info(f"Restarted browser instance {index}")


browser_pool = BrowserPool()
