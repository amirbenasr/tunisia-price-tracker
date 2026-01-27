"""Celery tasks for data cleanup and maintenance."""

import asyncio
from datetime import datetime, timedelta

import structlog
from celery import shared_task
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config import settings
from src.models import PriceRecord, ScrapeLog

logger = structlog.get_logger()


def get_async_session() -> async_sessionmaker[AsyncSession]:
    """Create async session factory for tasks."""
    engine = create_async_engine(settings.database_url)
    return async_sessionmaker(engine, expire_on_commit=False)


@shared_task
def cleanup_old_prices(days: int = 90) -> dict:
    """
    Clean up old price records beyond retention period.

    TimescaleDB handles this automatically with retention policies,
    but this provides manual cleanup capability.

    Args:
        days: Number of days of price history to retain

    Returns:
        Dictionary with cleanup results
    """
    return asyncio.run(_cleanup_old_prices_async(days))


async def _cleanup_old_prices_async(days: int) -> dict:
    """Async implementation of price cleanup."""
    session_factory = get_async_session()
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    async with session_factory() as db:
        # Count records to delete
        count_stmt = select(func.count(PriceRecord.id)).where(
            PriceRecord.recorded_at < cutoff_date
        )
        result = await db.execute(count_stmt)
        count = result.scalar() or 0

        if count == 0:
            logger.info("No old price records to clean up")
            return {"deleted": 0, "cutoff_date": cutoff_date.isoformat()}

        # Delete old records
        # Note: For TimescaleDB, you might use drop_chunks() instead
        delete_stmt = delete(PriceRecord).where(
            PriceRecord.recorded_at < cutoff_date
        )
        await db.execute(delete_stmt)
        await db.commit()

        logger.info(
            "Cleaned up old price records",
            deleted=count,
            cutoff_date=cutoff_date.isoformat(),
        )

        return {
            "deleted": count,
            "cutoff_date": cutoff_date.isoformat(),
        }


@shared_task
def cleanup_old_scrape_logs(days: int = 30) -> dict:
    """
    Clean up old scrape logs.

    Args:
        days: Number of days of logs to retain

    Returns:
        Dictionary with cleanup results
    """
    return asyncio.run(_cleanup_old_logs_async(days))


async def _cleanup_old_logs_async(days: int) -> dict:
    """Async implementation of log cleanup."""
    session_factory = get_async_session()
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    async with session_factory() as db:
        # Count logs to delete
        count_stmt = select(func.count(ScrapeLog.id)).where(
            ScrapeLog.started_at < cutoff_date
        )
        result = await db.execute(count_stmt)
        count = result.scalar() or 0

        if count == 0:
            return {"deleted": 0, "cutoff_date": cutoff_date.isoformat()}

        # Delete old logs
        delete_stmt = delete(ScrapeLog).where(ScrapeLog.started_at < cutoff_date)
        await db.execute(delete_stmt)
        await db.commit()

        logger.info(
            "Cleaned up old scrape logs",
            deleted=count,
            cutoff_date=cutoff_date.isoformat(),
        )

        return {
            "deleted": count,
            "cutoff_date": cutoff_date.isoformat(),
        }


@shared_task
def update_website_stats() -> dict:
    """Update product counts for all websites."""
    return asyncio.run(_update_stats_async())


async def _update_stats_async() -> dict:
    """Async implementation of stats update."""
    from src.models import Website, Product
    from sqlalchemy import update

    session_factory = get_async_session()

    async with session_factory() as db:
        # Get all websites
        stmt = select(Website)
        result = await db.execute(stmt)
        websites = result.scalars().all()

        updated = 0
        for website in websites:
            # Count active products
            count_stmt = select(func.count(Product.id)).where(
                Product.website_id == website.id,
                Product.is_active == True,
            )
            result = await db.execute(count_stmt)
            count = result.scalar() or 0

            # Update if different
            if website.total_products != count:
                website.total_products = count
                updated += 1

        await db.commit()

        return {
            "websites_checked": len(websites),
            "websites_updated": updated,
        }
