"""Base scraper class defining the interface for all scrapers."""

import asyncio
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import structlog
from playwright.async_api import Page

logger = structlog.get_logger()


@dataclass
class ScrapedProduct:
    """Data class representing a scraped product."""

    external_id: str
    name: str
    product_url: str
    price: Decimal
    original_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    ean_code: Optional[str] = None
    in_stock: bool = True
    category: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapeResult:
    """Result of a scrape operation."""

    products: List[ScrapedProduct] = field(default_factory=list)
    pages_scraped: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.

    Defines the interface that all scrapers must implement.
    Provides common utilities for parsing and data extraction.
    """

    def __init__(
        self,
        website_name: str,
        base_url: str,
        rate_limit_ms: int = 1000,
    ):
        self.website_name = website_name
        self.base_url = base_url
        self.rate_limit_ms = rate_limit_ms
        self.logger = logger.bind(scraper=website_name)

    @abstractmethod
    async def scrape(self, page: Page, max_pages: int = 50) -> ScrapeResult:
        """
        Execute the scraping logic.

        Args:
            page: Playwright page instance
            max_pages: Maximum pages to scrape

        Returns:
            ScrapeResult with products and metadata
        """
        pass

    async def wait_between_requests(self) -> None:
        """Wait for the configured rate limit."""
        await asyncio.sleep(self.rate_limit_ms / 1000)

    def resolve_url(self, url: str) -> str:
        """Resolve a relative URL to absolute."""
        if url.startswith("http"):
            return url
        return urljoin(self.base_url, url)

    def generate_external_id(self, url: str) -> str:
        """Generate a unique external ID from a product URL."""
        # Extract path and create a hash
        clean_url = url.split("?")[0].rstrip("/")
        return hashlib.md5(clean_url.encode()).hexdigest()[:16]

    def parse_price(self, price_text: str) -> Optional[Decimal]:
        """
        Parse price text into a Decimal.

        Handles various formats:
        - "45.900 TND"
        - "45,900 DT"
        - "45.90€"
        - "45 900"
        """
        if not price_text:
            return None

        try:
            # Remove currency symbols and words
            cleaned = re.sub(r"[^\d.,\s]", "", price_text)
            cleaned = cleaned.strip()

            if not cleaned:
                return None

            # Handle space as thousand separator (e.g., "45 900")
            if " " in cleaned and "," not in cleaned and "." not in cleaned:
                cleaned = cleaned.replace(" ", "")

            # Handle comma as decimal separator (European format)
            if "," in cleaned and "." not in cleaned:
                cleaned = cleaned.replace(",", ".")
            elif "," in cleaned and "." in cleaned:
                # Both present - comma is thousand separator
                cleaned = cleaned.replace(",", "")

            # Remove thousand separators (spaces)
            cleaned = cleaned.replace(" ", "")

            return Decimal(cleaned)
        except (InvalidOperation, ValueError) as e:
            self.logger.warning("Failed to parse price", text=price_text, error=str(e))
            return None

    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text."""
        if not text:
            return None
        # Normalize whitespace
        cleaned = " ".join(text.split())
        return cleaned.strip() if cleaned else None

    def is_in_stock(self, stock_text: Optional[str], stock_element_exists: bool = True) -> bool:
        """
        Determine stock status from text or element presence.

        Common patterns:
        - "In Stock", "En stock", "Disponible"
        - "Out of Stock", "Rupture", "Indisponible"
        """
        if not stock_element_exists:
            return True  # Assume in stock if no indicator

        if not stock_text:
            return stock_element_exists

        text_lower = stock_text.lower()

        out_of_stock_patterns = [
            "out of stock",
            "rupture",
            "indisponible",
            "épuisé",
            "non disponible",
            "unavailable",
        ]

        for pattern in out_of_stock_patterns:
            if pattern in text_lower:
                return False

        return True

    def extract_brand(self, text: str, known_brands: Optional[List[str]] = None) -> Optional[str]:
        """Try to extract brand from product name or text."""
        if known_brands:
            text_lower = text.lower()
            for brand in known_brands:
                if brand.lower() in text_lower:
                    return brand
        return None


class ScraperRegistry:
    """Registry for custom scraper classes."""

    _scrapers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a scraper class."""

        def decorator(scraper_class: type):
            cls._scrapers[name] = scraper_class
            return scraper_class

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """Get a scraper class by name."""
        return cls._scrapers.get(name)

    @classmethod
    def list_scrapers(cls) -> List[str]:
        """List all registered scraper names."""
        return list(cls._scrapers.keys())
