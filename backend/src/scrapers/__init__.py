"""Scraping infrastructure."""

from src.scrapers.base import BaseScraper, ScrapedProduct, ScrapeResult
from src.scrapers.browser import BrowserPool, get_browser_pool, close_browser_pool
from src.scrapers.config_driven import ConfigDrivenScraper, create_scraper_from_config
from src.scrapers.registry import ScraperRegistry, get_scraper_for_website

__all__ = [
    "BaseScraper",
    "ScrapedProduct",
    "ScrapeResult",
    "BrowserPool",
    "get_browser_pool",
    "close_browser_pool",
    "ConfigDrivenScraper",
    "create_scraper_from_config",
    "ScraperRegistry",
    "get_scraper_for_website",
]
