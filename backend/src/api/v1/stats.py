"""Statistics and analytics API endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import DBSession
from src.models import PriceRecord, Product, ScrapeLog, Website
from src.schemas.common import BaseSchema

router = APIRouter(prefix="/stats", tags=["Statistics"])


class DashboardStats(BaseSchema):
    """Dashboard statistics."""

    total_websites: int
    active_websites: int
    total_products: int
    total_price_records: int
    scrapes_today: int
    scrapes_success_rate: float
    products_added_today: int
    price_changes_today: int


class WebsiteSummary(BaseSchema):
    """Summary of a website for stats."""

    id: str
    name: str
    total_products: int
    last_scraped_at: Optional[datetime]
    is_active: bool


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: DBSession):
    """
    Get aggregated statistics for the dashboard.

    Returns counts and metrics useful for monitoring the system health.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total websites
    websites_stmt = select(func.count(Website.id))
    websites_result = await db.execute(websites_stmt)
    total_websites = websites_result.scalar() or 0

    # Active websites
    active_stmt = select(func.count(Website.id)).where(Website.is_active == True)
    active_result = await db.execute(active_stmt)
    active_websites = active_result.scalar() or 0

    # Total products
    products_stmt = select(func.count(Product.id)).where(Product.is_active == True)
    products_result = await db.execute(products_stmt)
    total_products = products_result.scalar() or 0

    # Total price records
    prices_stmt = select(func.count(PriceRecord.id))
    prices_result = await db.execute(prices_stmt)
    total_price_records = prices_result.scalar() or 0

    # Scrapes today
    scrapes_today_stmt = select(func.count(ScrapeLog.id)).where(
        ScrapeLog.started_at >= today
    )
    scrapes_today_result = await db.execute(scrapes_today_stmt)
    scrapes_today = scrapes_today_result.scalar() or 0

    # Success rate (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    total_scrapes_stmt = select(func.count(ScrapeLog.id)).where(
        ScrapeLog.started_at >= week_ago
    )
    total_scrapes_result = await db.execute(total_scrapes_stmt)
    total_scrapes = total_scrapes_result.scalar() or 0

    success_scrapes_stmt = select(func.count(ScrapeLog.id)).where(
        ScrapeLog.started_at >= week_ago,
        ScrapeLog.status == "success",
    )
    success_scrapes_result = await db.execute(success_scrapes_stmt)
    success_scrapes = success_scrapes_result.scalar() or 0

    success_rate = (success_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0

    # Products added today
    products_today_stmt = select(func.count(Product.id)).where(
        Product.created_at >= today
    )
    products_today_result = await db.execute(products_today_stmt)
    products_added_today = products_today_result.scalar() or 0

    # Price changes today
    price_changes_stmt = select(func.count(PriceRecord.id)).where(
        PriceRecord.recorded_at >= today
    )
    price_changes_result = await db.execute(price_changes_stmt)
    price_changes_today = price_changes_result.scalar() or 0

    return DashboardStats(
        total_websites=total_websites,
        active_websites=active_websites,
        total_products=total_products,
        total_price_records=total_price_records,
        scrapes_today=scrapes_today,
        scrapes_success_rate=round(success_rate, 2),
        products_added_today=products_added_today,
        price_changes_today=price_changes_today,
    )


@router.get("/websites-summary")
async def get_websites_summary(
    db: DBSession,
    limit: int = Query(default=10, ge=1, le=50),
):
    """Get summary of all websites with basic stats."""
    stmt = (
        select(Website)
        .order_by(Website.total_products.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    websites = result.scalars().all()

    return [
        WebsiteSummary(
            id=str(w.id),
            name=w.name,
            total_products=w.total_products,
            last_scraped_at=w.last_scraped_at,
            is_active=w.is_active,
        )
        for w in websites
    ]
