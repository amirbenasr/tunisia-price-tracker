"""Browser pool management for Playwright-based scraping."""

import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional

import structlog
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from src.core.config import settings

logger = structlog.get_logger()


class BrowserPool:
    """
    Manages a pool of Playwright browser instances.

    Provides controlled access to browsers with concurrency limits
    and automatic cleanup.
    """

    def __init__(
        self,
        max_browsers: int = 3,
        headless: bool = True,
    ):
        self.max_browsers = max_browsers
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._semaphore = asyncio.Semaphore(max_browsers)
        self._lock = asyncio.Lock()
        self._context_count = 0

    async def initialize(self) -> None:
        """Initialize the browser pool."""
        async with self._lock:
            if self._playwright is None:
                logger.info("Initializing browser pool", max_browsers=self.max_browsers)
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )
                logger.info("Browser pool initialized")

    async def close(self) -> None:
        """Close all browsers and cleanup."""
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Browser pool closed")

    @asynccontextmanager
    async def get_page(self, timeout_ms: int = 30000):
        """
        Get a browser page from the pool.

        Usage:
            async with browser_pool.get_page() as page:
                await page.goto(url)
                # ... scrape
        """
        await self.initialize()

        async with self._semaphore:
            context: Optional[BrowserContext] = None
            page: Optional[Page] = None

            try:
                # Create a new context for isolation
                context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=self._get_user_agent(),
                    java_script_enabled=True,
                    ignore_https_errors=True,
                )

                # Set default timeout
                context.set_default_timeout(timeout_ms)

                # Create page
                page = await context.new_page()

                # Block unnecessary resources for faster loading
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}",
                    lambda route: route.abort(),
                )

                self._context_count += 1
                logger.debug("Page acquired", context_count=self._context_count)

                yield page

            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()
                self._context_count -= 1
                logger.debug("Page released", context_count=self._context_count)

    @asynccontextmanager
    async def get_page_with_images(self, timeout_ms: int = 30000):
        """Get a page that loads images (for screenshot/visual scraping)."""
        await self.initialize()

        async with self._semaphore:
            context: Optional[BrowserContext] = None
            page: Optional[Page] = None

            try:
                context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=self._get_user_agent(),
                    java_script_enabled=True,
                    ignore_https_errors=True,
                )
                context.set_default_timeout(timeout_ms)
                page = await context.new_page()

                self._context_count += 1
                yield page

            finally:
                if page:
                    await page.close()
                if context:
                    await context.close()
                self._context_count -= 1

    def _get_user_agent(self) -> str:
        """Get a realistic user agent string."""
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )


# Global browser pool instance
_browser_pool: Optional[BrowserPool] = None


async def get_browser_pool() -> BrowserPool:
    """Get or create the global browser pool."""
    global _browser_pool
    if _browser_pool is None:
        _browser_pool = BrowserPool(
            max_browsers=settings.max_concurrent_browsers,
            headless=settings.browser_headless,
        )
    return _browser_pool


async def close_browser_pool() -> None:
    """Close the global browser pool."""
    global _browser_pool
    if _browser_pool is not None:
        await _browser_pool.close()
        _browser_pool = None
