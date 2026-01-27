"""Scraper registry and factory."""

from typing import Dict, Optional, Type

import structlog

from src.scrapers.base import BaseScraper

logger = structlog.get_logger()


class ScraperRegistry:
    """
    Registry for custom scraper implementations.

    Custom scrapers are registered by name and can be instantiated
    for websites that require specialized scraping logic.
    """

    _scrapers: Dict[str, Type[BaseScraper]] = {}

    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a custom scraper class.

        Usage:
            @ScraperRegistry.register("mytek")
            class MyTekScraper(BaseScraper):
                ...
        """

        def decorator(scraper_class: Type[BaseScraper]) -> Type[BaseScraper]:
            cls._scrapers[name.lower()] = scraper_class
            logger.info("Registered custom scraper", name=name)
            return scraper_class

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseScraper]]:
        """Get a scraper class by name."""
        return cls._scrapers.get(name.lower())

    @classmethod
    def list_scrapers(cls) -> list:
        """List all registered scraper names."""
        return list(cls._scrapers.keys())

    @classmethod
    def has_scraper(cls, name: str) -> bool:
        """Check if a scraper is registered."""
        return name.lower() in cls._scrapers


def get_scraper_for_website(
    website_name: str,
    scraper_type: str,
    base_url: str,
    config: dict,
    rate_limit_ms: int = 1000,
) -> BaseScraper:
    """
    Factory function to get the appropriate scraper for a website.

    Args:
        website_name: Name of the website
        scraper_type: Type of scraper ('config_driven' or custom name)
        base_url: Base URL of the website
        config: Scraper configuration (selectors, pagination, etc.)
        rate_limit_ms: Rate limit between requests

    Returns:
        Configured scraper instance
    """
    from src.scrapers.config_driven import ConfigDrivenScraper

    if scraper_type == "config_driven":
        return ConfigDrivenScraper(
            website_name=website_name,
            base_url=base_url,
            selectors=config.get("selectors", {}),
            pagination_config=config.get("pagination_config"),
            rate_limit_ms=rate_limit_ms,
        )

    # Check for custom scraper
    scraper_class = ScraperRegistry.get(scraper_type)
    if scraper_class:
        return scraper_class(
            website_name=website_name,
            base_url=base_url,
            rate_limit_ms=rate_limit_ms,
        )

    # Fallback to config-driven
    logger.warning(
        "Unknown scraper type, falling back to config_driven",
        scraper_type=scraper_type,
        website=website_name,
    )
    return ConfigDrivenScraper(
        website_name=website_name,
        base_url=base_url,
        selectors=config.get("selectors", {}),
        pagination_config=config.get("pagination_config"),
        rate_limit_ms=rate_limit_ms,
    )


# Import custom scrapers to register them
# from src.scrapers.sites import *  # noqa
