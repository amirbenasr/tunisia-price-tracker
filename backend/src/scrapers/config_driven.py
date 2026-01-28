"""Config-driven scraper using CSS selectors from database."""

import asyncio
from decimal import Decimal
from typing import Any, Dict, List, Optional

import structlog
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.scrapers.base import BaseScraper, ScrapedProduct, ScrapeResult

logger = structlog.get_logger()


class ConfigDrivenScraper(BaseScraper):
    """
    Generic scraper that uses CSS selectors from configuration.

    This allows scraping most websites without writing custom code.
    Selectors are stored in the database and can be updated via admin UI.
    """

    def __init__(
        self,
        website_name: str,
        base_url: str,
        selectors: Dict[str, Any],
        pagination_config: Optional[Dict[str, Any]] = None,
        rate_limit_ms: int = 1000,
    ):
        super().__init__(website_name, base_url, rate_limit_ms)
        self.selectors = selectors
        self.pagination_config = pagination_config or {}

    async def scrape(self, page: Page, max_pages: int = 50) -> ScrapeResult:
        """Scrape products using configured selectors."""
        result = ScrapeResult()
        current_url = self.base_url
        pages_scraped = 0

        self.logger.info("Starting scrape", url=current_url, max_pages=max_pages)

        # Get wait strategy from config
        wait_for_selector = self.selectors.get("wait_for_selector")

        while pages_scraped < max_pages:
            try:
                # Navigate to page with configured wait strategy
                if wait_for_selector:
                    await page.goto(current_url, timeout=30000)
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=15000)
                    except PlaywrightTimeout:
                        self.logger.warning("Wait selector timeout", url=current_url, selector=wait_for_selector)
                else:
                    # Fallback to networkidle
                    await page.goto(current_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(0.5)  # Brief wait for dynamic content

                # Extract products from current page
                products = await self._extract_products(page)
                result.products.extend(products)
                pages_scraped += 1

                self.logger.info(
                    "Page scraped",
                    page=pages_scraped,
                    products_found=len(products),
                    total_products=len(result.products),
                )

                # Get next page URL
                next_url = await self._get_next_page_url(page)
                if not next_url:
                    self.logger.info("No more pages")
                    break

                current_url = next_url
                await self.wait_between_requests()

            except PlaywrightTimeout as e:
                error = {
                    "type": "timeout",
                    "page": pages_scraped + 1,
                    "url": current_url,
                    "message": str(e),
                }
                result.errors.append(error)
                self.logger.warning("Page timeout", **error)
                break

            except Exception as e:
                error = {
                    "type": "error",
                    "page": pages_scraped + 1,
                    "url": current_url,
                    "message": str(e),
                }
                result.errors.append(error)
                self.logger.error("Scrape error", **error, exc_info=e)
                break

        result.pages_scraped = pages_scraped
        result.success = len(result.errors) == 0

        self.logger.info(
            "Scrape completed",
            pages_scraped=pages_scraped,
            total_products=len(result.products),
            errors=len(result.errors),
        )

        return result

    async def _extract_products(self, page: Page) -> List[ScrapedProduct]:
        """Extract products from the current page."""
        products = []

        # Get the container and item selectors
        container_selector = self.selectors.get("container", "body")
        item_selector = self.selectors.get("item", ".product")

        # Find all product items
        items = await page.query_selector_all(f"{container_selector} {item_selector}")

        for item in items:
            try:
                product = await self._extract_single_product(item, page)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.warning("Failed to extract product", error=str(e))
                continue

        return products

    async def _extract_single_product(self, item, page: Page) -> Optional[ScrapedProduct]:
        """Extract data for a single product."""
        # Extract name
        name = await self._get_text(item, self.selectors.get("name"))
        if not name:
            return None

        # Extract URL
        url = await self._get_attribute(item, self.selectors.get("url"), "href")
        if not url:
            return None
        url = self.resolve_url(url)

        # Extract price
        price_text = await self._get_text(item, self.selectors.get("price"))
        price = self.parse_price(price_text) if price_text else None
        if not price:
            return None

        # Extract original price (for discounts)
        original_price_text = await self._get_text(
            item, self.selectors.get("original_price")
        )
        original_price = self.parse_price(original_price_text) if original_price_text else None

        # Extract image
        image_url = await self._get_attribute(
            item, self.selectors.get("image"), "src"
        )
        if image_url:
            image_url = self.resolve_url(image_url)

        # Extract stock status
        stock_selector = self.selectors.get("in_stock")
        in_stock = True
        if stock_selector:
            stock_element = await item.query_selector(stock_selector)
            if stock_element:
                stock_text = await stock_element.inner_text()
                in_stock = self.is_in_stock(stock_text)

        # Extract brand
        brand = await self._get_text(item, self.selectors.get("brand"))

        # Extract SKU
        sku = await self._get_text(item, self.selectors.get("sku"))

        # Generate external ID
        external_id = self.generate_external_id(url)

        return ScrapedProduct(
            external_id=external_id,
            name=self.clean_text(name),
            product_url=url,
            price=price,
            original_price=original_price,
            image_url=image_url,
            brand=self.clean_text(brand),
            sku=self.clean_text(sku),
            in_stock=in_stock,
        )

    async def _get_text(self, element, selector: Optional[str]) -> Optional[str]:
        """Get text content from an element using a selector."""
        if not selector:
            return None

        try:
            child = await element.query_selector(selector)
            if child:
                return await child.inner_text()
        except Exception:
            pass
        return None

    async def _get_attribute(
        self, element, selector: Optional[str], attribute: str
    ) -> Optional[str]:
        """Get attribute value from an element using a selector."""
        if not selector:
            return None

        try:
            # Handle ::attr() pseudo-selector
            if "::attr(" in selector:
                base_selector, attr = selector.rsplit("::attr(", 1)
                attr = attr.rstrip(")")
                child = await element.query_selector(base_selector)
                if child:
                    return await child.get_attribute(attr)
            else:
                child = await element.query_selector(selector)
                if child:
                    return await child.get_attribute(attribute)
        except Exception:
            pass
        return None

    async def _get_next_page_url(self, page: Page) -> Optional[str]:
        """Get the URL for the next page using pagination config."""
        pagination_type = self.pagination_config.get("type", "next_button")

        if pagination_type == "next_button":
            next_selector = self.pagination_config.get("next_selector")
            if next_selector:
                # Handle ::attr() in selector
                if "::attr(" in next_selector:
                    base_selector, attr = next_selector.rsplit("::attr(", 1)
                    attr = attr.rstrip(")")
                    element = await page.query_selector(base_selector)
                    if element:
                        href = await element.get_attribute(attr)
                        if href:
                            return self.resolve_url(href)
                else:
                    element = await page.query_selector(next_selector)
                    if element:
                        href = await element.get_attribute("href")
                        if href:
                            return self.resolve_url(href)

        elif pagination_type == "page_number":
            # Implement page number based pagination
            # This would track current page and increment
            pass

        elif pagination_type == "infinite_scroll":
            # Implement infinite scroll handling
            # Scroll to bottom and wait for content
            pass

        return None


async def create_scraper_from_config(
    website_name: str,
    base_url: str,
    config: Dict[str, Any],
    rate_limit_ms: int = 1000,
) -> ConfigDrivenScraper:
    """Factory function to create a config-driven scraper."""
    return ConfigDrivenScraper(
        website_name=website_name,
        base_url=base_url,
        selectors=config.get("selectors", {}),
        pagination_config=config.get("pagination_config"),
        rate_limit_ms=rate_limit_ms,
    )
