"""Celery tasks."""

from workers.tasks.cleanup import cleanup_old_prices, cleanup_old_scrape_logs, update_website_stats
from workers.tasks.scrape import scrape_website, scrape_all_websites

__all__ = [
    "scrape_website",
    "scrape_all_websites",
    "cleanup_old_prices",
    "cleanup_old_scrape_logs",
    "update_website_stats",
]
