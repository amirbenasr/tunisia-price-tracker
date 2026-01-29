"""Celery tasks for web scraping."""

import asyncio
from datetime import datetime
from typing import Awaitable, Callable, Optional
from uuid import UUID

import redis.asyncio as aioredis
import structlog
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config import settings
from src.core.redis import TaskCancellation
from src.models import Product, ScraperConfig, ScrapeLog, Website
from src.models.price import PriceRecord
from src.scrapers import get_browser_pool, close_browser_pool, get_scraper_for_website
from src.scrapers.sitemap import SitemapScraper

logger = structlog.get_logger()


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Create async session factory for tasks."""
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_website(self, website_id: str, log_id: Optional[str] = None) -> dict:
    """
    Scrape a single website.

    Args:
        website_id: UUID of the website to scrape
        log_id: Optional UUID of existing scrape log

    Returns:
        Dictionary with scrape results
    """
    return asyncio.run(_scrape_website_async(website_id, log_id, self.request.id))


async def _scrape_website_async(
    website_id: str,
    log_id: Optional[str],
    task_id: str,
) -> dict:
    """Async implementation of website scraping."""
    session_factory = get_async_session()

    # Create Redis client for cancellation checking
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    cancellation_service = TaskCancellation(redis_client)

    # Async cancellation checker callback for this task
    async def is_cancelled() -> bool:
        return await cancellation_service.is_cancelled(task_id)

    try:
        return await _do_scrape(
            session_factory, website_id, log_id, task_id, is_cancelled
        )
    finally:
        # Always cleanup Redis connection and cancellation flag
        await cancellation_service.clear_cancellation(task_id)
        await redis_client.close()


async def _do_scrape(
    session_factory,
    website_id: str,
    log_id: Optional[str],
    task_id: str,
    is_cancelled: Callable[[], Awaitable[bool]],
) -> dict:
    """Actual scraping logic, separated for cleaner cleanup handling."""
    async with session_factory() as db:
        # Get website
        stmt = select(Website).where(Website.id == UUID(website_id))
        result = await db.execute(stmt)
        website = result.scalar_one_or_none()

        if not website:
            return {"error": f"Website {website_id} not found"}

        if not website.is_active:
            return {"error": f"Website {website.name} is not active"}

        # Get or create scrape log
        if log_id:
            stmt = select(ScrapeLog).where(ScrapeLog.id == UUID(log_id))
            result = await db.execute(stmt)
            log = result.scalar_one_or_none()
        else:
            log = ScrapeLog(
                website_id=website.id,
                started_at=datetime.utcnow(),
                triggered_by="celery",
                celery_task_id=task_id,
                status="running",
            )
            db.add(log)
            await db.commit()

        # Get scraper config (either product_list or sitemap)
        stmt = select(ScraperConfig).where(
            ScraperConfig.website_id == website.id,
            ScraperConfig.is_active == True,
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            log.status = "failed"
            log.completed_at = datetime.utcnow()
            log.errors = [{"type": "config_error", "message": "No active scraper config found"}]
            await db.commit()
            return {"error": "No scraper config found"}

        # Create scraper based on config type
        if config.config_type == "sitemap":
            # Sitemap-based scraper
            scraper = SitemapScraper(
                website_name=website.name,
                base_url=website.base_url,
                sitemap_config=config.sitemap_config or {},
                selectors=config.selectors or {},
                rate_limit_ms=website.rate_limit_ms,
                last_scraped_at=website.last_scraped_at,
            )
            logger.info(
                "Using sitemap scraper",
                website=website.name,
                sitemap_url=config.sitemap_config.get("sitemap_url") if config.sitemap_config else None,
            )
        else:
            # CSS-based scraper (product_list)
            scraper = get_scraper_for_website(
                website_name=website.name,
                scraper_type=website.scraper_type,
                base_url=website.base_url,
                config={
                    "selectors": config.selectors,
                    "pagination_config": config.pagination_config,
                },
                rate_limit_ms=website.rate_limit_ms,
            )
            logger.info("Using CSS-based scraper", website=website.name)

        # Get browser and scrape
        browser_pool = await get_browser_pool()

        try:
            async with browser_pool.get_page() as page:
                scrape_result = await scraper.scrape(page, max_pages=50, is_cancelled=is_cancelled)

            # Process results
            products_created = 0
            products_updated = 0
            prices_recorded = 0

            for scraped in scrape_result.products:
                # Upsert product
                stmt = select(Product).where(
                    Product.website_id == website.id,
                    Product.external_id == scraped.external_id,
                )
                result = await db.execute(stmt)
                product = result.scalar_one_or_none()

                if product:
                    # Update existing
                    product.name = scraped.name
                    product.product_url = scraped.product_url
                    product.image_url = scraped.image_url
                    product.brand = scraped.brand
                    product.is_active = True
                    products_updated += 1
                else:
                    # Create new
                    product = Product(
                        website_id=website.id,
                        external_id=scraped.external_id,
                        name=scraped.name,
                        product_url=scraped.product_url,
                        image_url=scraped.image_url,
                        brand=scraped.brand,
                    )
                    db.add(product)
                    await db.flush()  # Get product ID
                    products_created += 1

                # Record price
                price_record = PriceRecord(
                    product_id=product.id,
                    price=scraped.price,
                    original_price=scraped.original_price,
                    in_stock=scraped.in_stock,
                    currency="TND",
                )
                db.add(price_record)
                prices_recorded += 1

            # Update log status based on result
            if scrape_result.cancelled:
                log.status = "cancelled"
            elif scrape_result.success:
                log.status = "success"
            else:
                log.status = "partial"
            log.completed_at = datetime.utcnow()
            log.products_found = len(scrape_result.products)
            log.products_created = products_created
            log.products_updated = products_updated
            log.prices_recorded = prices_recorded
            log.pages_scraped = scrape_result.pages_scraped
            log.errors = scrape_result.errors

            # Update website stats
            website.last_scraped_at = datetime.utcnow()
            website.total_products = products_created + products_updated

            await db.commit()

            logger.info(
                "Scrape completed",
                website=website.name,
                products_found=len(scrape_result.products),
                created=products_created,
                updated=products_updated,
            )

            return {
                "website": website.name,
                "status": log.status,
                "products_found": len(scrape_result.products),
                "products_created": products_created,
                "products_updated": products_updated,
                "prices_recorded": prices_recorded,
                "pages_scraped": scrape_result.pages_scraped,
            }

        except Exception as e:
            log.status = "failed"
            log.completed_at = datetime.utcnow()
            log.errors = [{"type": "exception", "message": str(e)}]
            await db.commit()

            logger.error("Scrape failed", website=website.name, error=str(e), exc_info=e)
            raise


@shared_task
def scrape_all_websites() -> dict:
    """Scrape all active websites."""
    return asyncio.run(_scrape_all_websites_async())


async def _scrape_all_websites_async() -> dict:
    """Async implementation of scraping all websites."""
    session_factory = get_async_session()
    results = []

    async with session_factory() as db:
        stmt = select(Website).where(Website.is_active == True)
        result = await db.execute(stmt)
        websites = result.scalars().all()

    for website in websites:
        try:
            result = await _scrape_website_async(str(website.id), None, "batch")
            results.append(result)
        except Exception as e:
            results.append({
                "website": website.name,
                "status": "failed",
                "error": str(e),
            })

    # Close browser pool
    await close_browser_pool()

    return {
        "total_websites": len(websites),
        "results": results,
    }
