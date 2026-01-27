"""
Example custom scraper implementation.

Use this as a template for creating custom scrapers for complex websites
that can't be handled by the config-driven scraper.
"""

from typing import List

from playwright.async_api import Page

from src.scrapers.base import BaseScraper, ScrapedProduct, ScrapeResult
from src.scrapers.registry import ScraperRegistry


# Uncomment the decorator to register this scraper
# @ScraperRegistry.register("example_site")
class ExampleSiteScraper(BaseScraper):
    """
    Custom scraper for example-site.tn

    This scraper handles specific requirements like:
    - Custom anti-bot bypass
    - Login requirements
    - Complex dynamic content loading
    - Non-standard pagination
    """

    async def scrape(self, page: Page, max_pages: int = 50) -> ScrapeResult:
        """Execute custom scraping logic."""
        result = ScrapeResult()

        try:
            # Custom navigation logic
            await page.goto(self.base_url, wait_until="networkidle")

            # Handle any anti-bot measures
            await self._handle_antibot(page)

            # Scrape products
            for page_num in range(1, max_pages + 1):
                products = await self._scrape_page(page)
                result.products.extend(products)
                result.pages_scraped += 1

                self.logger.info(
                    "Page scraped",
                    page=page_num,
                    products=len(products),
                )

                # Navigate to next page
                has_next = await self._go_to_next_page(page)
                if not has_next:
                    break

                await self.wait_between_requests()

            result.success = True

        except Exception as e:
            result.errors.append({
                "type": "error",
                "message": str(e),
            })
            result.success = False
            self.logger.error("Scrape failed", error=str(e), exc_info=e)

        return result

    async def _handle_antibot(self, page: Page) -> None:
        """Handle any anti-bot challenges."""
        # Example: Wait for challenge to complete
        # await page.wait_for_selector(".cf-browser-verification", state="hidden")
        pass

    async def _scrape_page(self, page: Page) -> List[ScrapedProduct]:
        """Scrape products from current page."""
        products = []

        # Example product extraction
        items = await page.query_selector_all(".product-item")

        for item in items:
            try:
                name = await item.query_selector(".product-name")
                name_text = await name.inner_text() if name else None

                price_el = await item.query_selector(".product-price")
                price_text = await price_el.inner_text() if price_el else None

                link = await item.query_selector("a.product-link")
                url = await link.get_attribute("href") if link else None

                if name_text and price_text and url:
                    price = self.parse_price(price_text)
                    if price:
                        products.append(ScrapedProduct(
                            external_id=self.generate_external_id(url),
                            name=self.clean_text(name_text),
                            product_url=self.resolve_url(url),
                            price=price,
                        ))

            except Exception as e:
                self.logger.warning("Failed to extract product", error=str(e))
                continue

        return products

    async def _go_to_next_page(self, page: Page) -> bool:
        """Navigate to next page. Returns False if no more pages."""
        next_button = await page.query_selector(".pagination .next:not(.disabled)")

        if next_button:
            await next_button.click()
            await page.wait_for_load_state("networkidle")
            return True

        return False
