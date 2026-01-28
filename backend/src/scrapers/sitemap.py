"""Sitemap-based scraper for websites with sitemap.xml."""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import httpx
import structlog
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from src.scrapers.base import BaseScraper, ScrapedProduct, ScrapeResult

logger = structlog.get_logger()

# XML namespaces used in sitemaps
NAMESPACES = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}


@dataclass
class SitemapEntry:
    """A single URL entry from a sitemap."""

    loc: str
    lastmod: Optional[datetime] = None
    image_url: Optional[str] = None
    image_title: Optional[str] = None


class SitemapParser:
    """
    Generic sitemap parser that follows the sitemaps.org protocol.

    Handles both sitemap index files and direct urlset files.
    Works with any platform (Shopify, WooCommerce, Magento, etc.)
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.logger = logger.bind(component="SitemapParser")

    async def parse(
        self,
        sitemap_url: str,
        child_pattern: Optional[str] = None,
        url_include_pattern: Optional[str] = None,
        url_exclude_pattern: Optional[str] = None,
    ) -> List[SitemapEntry]:
        """
        Parse a sitemap and return filtered entries.

        Args:
            sitemap_url: The sitemap URL (can be index or urlset)
            child_pattern: Regex to filter child sitemaps (for sitemap index)
            url_include_pattern: Regex - only include URLs matching this
            url_exclude_pattern: Regex - exclude URLs matching this

        Returns:
            List of SitemapEntry objects
        """
        self.logger.info("Parsing sitemap", url=sitemap_url)

        content = await self._fetch(sitemap_url)
        if not content:
            return []

        # Parse XML
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            self.logger.error("Failed to parse sitemap XML", error=str(e))
            return []

        # Detect type and parse accordingly
        if self._is_sitemap_index(root):
            entries = await self._parse_sitemap_index(root, child_pattern)
        else:
            entries = self._parse_urlset(root)

        # Apply URL filters
        if url_include_pattern:
            include_re = re.compile(url_include_pattern, re.IGNORECASE)
            entries = [e for e in entries if include_re.search(e.loc)]

        if url_exclude_pattern:
            exclude_re = re.compile(url_exclude_pattern, re.IGNORECASE)
            entries = [e for e in entries if not exclude_re.search(e.loc)]

        self.logger.info("Sitemap parsed", total_urls=len(entries))
        return entries

    async def _fetch(self, url: str) -> Optional[str]:
        """Fetch sitemap content."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.text
        except Exception as e:
            self.logger.error("Failed to fetch sitemap", url=url, error=str(e))
            return None

    def _is_sitemap_index(self, root: ET.Element) -> bool:
        """Check if the root element is a sitemap index."""
        # Remove namespace for comparison
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        return tag == "sitemapindex"

    async def _parse_sitemap_index(
        self, root: ET.Element, child_pattern: Optional[str] = None
    ) -> List[SitemapEntry]:
        """Parse a sitemap index and fetch child sitemaps."""
        entries = []

        # Find all child sitemap URLs
        child_urls = []
        for sitemap in root.findall("sm:sitemap", NAMESPACES):
            loc = sitemap.find("sm:loc", NAMESPACES)
            if loc is not None and loc.text:
                child_urls.append(loc.text.strip())

        # Filter by pattern if specified
        if child_pattern:
            pattern = re.compile(child_pattern, re.IGNORECASE)
            child_urls = [u for u in child_urls if pattern.search(u)]

        self.logger.info("Found child sitemaps", count=len(child_urls))

        # Fetch and parse each child sitemap
        for url in child_urls:
            content = await self._fetch(url)
            if content:
                try:
                    child_root = ET.fromstring(content)
                    entries.extend(self._parse_urlset(child_root))
                except ET.ParseError as e:
                    self.logger.warning("Failed to parse child sitemap", url=url, error=str(e))

        return entries

    def _parse_urlset(self, root: ET.Element) -> List[SitemapEntry]:
        """Parse a urlset and extract entries."""
        entries = []

        for url in root.findall("sm:url", NAMESPACES):
            loc = url.find("sm:loc", NAMESPACES)
            if loc is None or not loc.text:
                continue

            entry = SitemapEntry(loc=loc.text.strip())

            # Parse lastmod if present
            lastmod = url.find("sm:lastmod", NAMESPACES)
            if lastmod is not None and lastmod.text:
                try:
                    # Handle various date formats
                    date_str = lastmod.text.strip()
                    if "T" in date_str:
                        # ISO format with time
                        entry.lastmod = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    else:
                        # Date only
                        entry.lastmod = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    pass

            # Parse image if present (common in Shopify sitemaps)
            image = url.find("image:image", NAMESPACES)
            if image is not None:
                image_loc = image.find("image:loc", NAMESPACES)
                if image_loc is not None and image_loc.text:
                    entry.image_url = image_loc.text.strip()

                image_title = image.find("image:title", NAMESPACES)
                if image_title is not None and image_title.text:
                    entry.image_title = image_title.text.strip()

            entries.append(entry)

        return entries


class SitemapScraper(BaseScraper):
    """
    Scraper that discovers products via sitemap and extracts data from product pages.

    Flow:
    1. Parse sitemap to get product URLs
    2. Filter by lastmod for incremental scraping (optional)
    3. Visit each product page and extract data using selectors
    """

    def __init__(
        self,
        website_name: str,
        base_url: str,
        sitemap_config: Dict[str, Any],
        selectors: Dict[str, Any],
        rate_limit_ms: int = 1000,
        last_scraped_at: Optional[datetime] = None,
    ):
        super().__init__(website_name, base_url, rate_limit_ms)
        self.sitemap_config = sitemap_config
        self.selectors = selectors
        self.last_scraped_at = last_scraped_at
        self.parser = SitemapParser()

    async def scrape(self, page: Page, max_pages: int = 300) -> ScrapeResult:
        """
        Scrape products discovered via sitemap.

        Args:
            page: Playwright page instance
            max_pages: Maximum number of product pages to visit

        Returns:
            ScrapeResult with products and metadata
        """
        result = ScrapeResult()

        # 1. Parse sitemap to get product URLs
        sitemap_url = self.sitemap_config.get("sitemap_url")
        if not sitemap_url:
            result.errors.append({"type": "config", "message": "No sitemap_url configured"})
            result.success = False
            return result

        entries = await self.parser.parse(
            sitemap_url=sitemap_url,
            child_pattern=self.sitemap_config.get("child_sitemap_pattern"),
            url_include_pattern=self.sitemap_config.get("url_include_pattern"),
            url_exclude_pattern=self.sitemap_config.get("url_exclude_pattern"),
        )

        if not entries:
            result.errors.append({"type": "sitemap", "message": "No URLs found in sitemap"})
            result.success = False
            return result

        self.logger.info("Found product URLs", count=len(entries))

        # 2. Filter by lastmod for incremental scraping
        if self.sitemap_config.get("use_lastmod") and self.last_scraped_at:
            original_count = len(entries)
            entries = [
                e for e in entries
                if e.lastmod is None or e.lastmod > self.last_scraped_at
            ]
            self.logger.info(
                "Filtered by lastmod",
                original=original_count,
                after_filter=len(entries),
                since=self.last_scraped_at.isoformat(),
            )

        # 3. Limit to max_pages
        if len(entries) > max_pages:
            self.logger.info("Limiting to max_pages", max_pages=max_pages)
            entries = entries[:max_pages]

        # 4. Visit each product page and extract data
        for i, entry in enumerate(entries):
            try:
                product = await self._scrape_product_page(page, entry)
                if product:
                    result.products.append(product)

                result.pages_scraped += 1

                if (i + 1) % 10 == 0:
                    self.logger.info(
                        "Progress",
                        scraped=i + 1,
                        total=len(entries),
                        products_found=len(result.products),
                    )

                await self.wait_between_requests()

            except PlaywrightTimeout as e:
                error = {"type": "timeout", "url": entry.loc, "message": str(e)}
                result.errors.append(error)
                self.logger.warning("Page timeout", **error)

            except Exception as e:
                error = {"type": "error", "url": entry.loc, "message": str(e)}
                result.errors.append(error)
                self.logger.warning("Scrape error", **error)

        result.success = len(result.errors) == 0 or len(result.products) > 0

        self.logger.info(
            "Scrape completed",
            pages_scraped=result.pages_scraped,
            products_found=len(result.products),
            errors=len(result.errors),
        )

        return result

    async def _scrape_product_page(
        self, page: Page, entry: SitemapEntry
    ) -> Optional[ScrapedProduct]:
        """Scrape a single product page."""
        # Get wait strategy from config
        wait_for_selector = self.selectors.get("wait_for_selector")

        if wait_for_selector:
            # Navigate and wait for specific element
            await page.goto(entry.loc, timeout=30000)
            try:
                await page.wait_for_selector(wait_for_selector, timeout=15000)
            except PlaywrightTimeout:
                self.logger.warning("Wait selector timeout", url=entry.loc, selector=wait_for_selector)
        else:
            # Fallback to networkidle
            await page.goto(entry.loc, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(0.3)  # Brief wait for dynamic content

        # Extract price (required)
        price_text = await self._get_text(page, self.selectors.get("price"))
        price = self.parse_price(price_text) if price_text else None
        if not price:
            self.logger.debug("No price found", url=entry.loc)
            return None

        # Use sitemap data if available, otherwise extract from page
        name = entry.image_title or await self._get_text(page, self.selectors.get("name"))
        if not name:
            # Try to get from page title
            name = await page.title()
            name = name.split("|")[0].strip() if name else None

        if not name:
            self.logger.debug("No name found", url=entry.loc)
            return None

        image_url = entry.image_url or await self._get_attribute(
            page, self.selectors.get("image"), "src"
        )

        # Extract optional fields
        original_price_text = await self._get_text(page, self.selectors.get("original_price"))
        original_price = self.parse_price(original_price_text) if original_price_text else None

        description = await self._get_text(page, self.selectors.get("description"))
        brand = await self._get_text(page, self.selectors.get("brand"))
        sku = await self._get_text(page, self.selectors.get("sku"))

        # Stock status
        in_stock = True
        stock_selector = self.selectors.get("in_stock")
        if stock_selector:
            stock_text = await self._get_text(page, stock_selector)
            if stock_text:
                in_stock = self.is_in_stock(stock_text)

        return ScrapedProduct(
            external_id=self.generate_external_id(entry.loc),
            name=self.clean_text(name),
            product_url=entry.loc,
            price=price,
            original_price=original_price,
            image_url=image_url,
            description=self.clean_text(description),
            brand=self.clean_text(brand),
            sku=self.clean_text(sku),
            in_stock=in_stock,
        )

    async def _get_text(self, page: Page, selector: Optional[str]) -> Optional[str]:
        """Get text content from page using selector."""
        if not selector:
            return None
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.inner_text()
        except Exception:
            pass
        return None

    async def _get_attribute(
        self, page: Page, selector: Optional[str], attribute: str
    ) -> Optional[str]:
        """Get attribute value from page using selector."""
        if not selector:
            return None
        try:
            # Handle ::attr() pseudo-selector
            if "::attr(" in selector:
                base_selector, attr = selector.rsplit("::attr(", 1)
                attr = attr.rstrip(")")
                element = await page.query_selector(base_selector)
                if element:
                    return await element.get_attribute(attr)
            else:
                element = await page.query_selector(selector)
                if element:
                    return await element.get_attribute(attribute)
        except Exception:
            pass
        return None


async def create_sitemap_scraper(
    website_name: str,
    base_url: str,
    sitemap_config: Dict[str, Any],
    selectors: Dict[str, Any],
    rate_limit_ms: int = 1000,
    last_scraped_at: Optional[datetime] = None,
) -> SitemapScraper:
    """Factory function to create a sitemap scraper."""
    return SitemapScraper(
        website_name=website_name,
        base_url=base_url,
        sitemap_config=sitemap_config,
        selectors=selectors,
        rate_limit_ms=rate_limit_ms,
        last_scraped_at=last_scraped_at,
    )
