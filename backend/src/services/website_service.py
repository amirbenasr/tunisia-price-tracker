"""Website service for CRUD operations on competitor websites."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PriceRecord, Product, ScrapeLog, Website
from src.schemas.website import (
    WebsiteCreate,
    WebsiteListResponse,
    WebsiteResponse,
    WebsiteStats,
    WebsiteUpdate,
)


class WebsiteService:
    """Service for managing competitor websites."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_website(self, website_id: UUID) -> Optional[Website]:
        """Get a website by ID."""
        stmt = select(Website).where(Website.id == website_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_website_by_name(self, name: str) -> Optional[Website]:
        """Get a website by name."""
        stmt = select(Website).where(Website.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_websites(
        self,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Website], int]:
        """Get all websites with optional filtering."""
        stmt = select(Website)

        if is_active is not None:
            stmt = stmt.where(Website.is_active == is_active)

        # Count total
        count_stmt = select(func.count(Website.id))
        if is_active is not None:
            count_stmt = count_stmt.where(Website.is_active == is_active)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Website.name).offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        websites = list(result.scalars().all())

        return websites, total

    async def get_active_websites(self) -> List[Website]:
        """Get all active websites for scraping."""
        stmt = (
            select(Website)
            .where(Website.is_active == True)
            .order_by(Website.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_website(self, data: WebsiteCreate) -> Website:
        """Create a new website."""
        website = Website(**data.model_dump())
        self.db.add(website)
        await self.db.commit()
        await self.db.refresh(website)
        return website

    async def update_website(
        self, website_id: UUID, data: WebsiteUpdate
    ) -> Optional[Website]:
        """Update an existing website."""
        website = await self.get_website(website_id)
        if not website:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(website, field, value)

        await self.db.commit()
        await self.db.refresh(website)
        return website

    async def delete_website(self, website_id: UUID) -> bool:
        """Delete a website and all related data."""
        website = await self.get_website(website_id)
        if not website:
            return False

        await self.db.delete(website)
        await self.db.commit()
        return True

    async def update_product_count(self, website_id: UUID) -> int:
        """Update the total_products count for a website."""
        count_stmt = select(func.count(Product.id)).where(
            and_(
                Product.website_id == website_id,
                Product.is_active == True,
            )
        )
        count_result = await self.db.execute(count_stmt)
        count = count_result.scalar() or 0

        await self.db.execute(
            update(Website)
            .where(Website.id == website_id)
            .values(total_products=count)
        )
        await self.db.commit()

        return count

    async def get_website_stats(self, website_id: UUID) -> Optional[WebsiteStats]:
        """Get detailed statistics for a website."""
        website = await self.get_website(website_id)
        if not website:
            return None

        # Count active products
        active_products_stmt = select(func.count(Product.id)).where(
            and_(
                Product.website_id == website_id,
                Product.is_active == True,
            )
        )
        active_result = await self.db.execute(active_products_stmt)
        active_products = active_result.scalar() or 0

        # Count total products
        total_products_stmt = select(func.count(Product.id)).where(
            Product.website_id == website_id
        )
        total_result = await self.db.execute(total_products_stmt)
        total_products = total_result.scalar() or 0

        # Count price records
        price_records_stmt = (
            select(func.count(PriceRecord.id))
            .join(Product, PriceRecord.product_id == Product.id)
            .where(Product.website_id == website_id)
        )
        price_result = await self.db.execute(price_records_stmt)
        total_price_records = price_result.scalar() or 0

        # Scrape statistics
        scrape_stats_stmt = select(
            func.count(ScrapeLog.id).label("total_scrapes"),
            func.avg(ScrapeLog.products_found).label("avg_products"),
        ).where(
            and_(
                ScrapeLog.website_id == website_id,
                ScrapeLog.status == "success",
            )
        )
        scrape_result = await self.db.execute(scrape_stats_stmt)
        scrape_row = scrape_result.first()

        # Success rate
        total_scrapes_stmt = select(func.count(ScrapeLog.id)).where(
            ScrapeLog.website_id == website_id
        )
        total_scrapes_result = await self.db.execute(total_scrapes_stmt)
        total_scrapes = total_scrapes_result.scalar() or 0

        success_scrapes_stmt = select(func.count(ScrapeLog.id)).where(
            and_(
                ScrapeLog.website_id == website_id,
                ScrapeLog.status == "success",
            )
        )
        success_scrapes_result = await self.db.execute(success_scrapes_stmt)
        success_scrapes = success_scrapes_result.scalar() or 0

        success_rate = (success_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0.0

        return WebsiteStats(
            total_products=total_products,
            active_products=active_products,
            total_price_records=total_price_records,
            last_scraped_at=website.last_scraped_at,
            avg_products_per_scrape=float(scrape_row.avg_products or 0) if scrape_row else 0.0,
            scrape_success_rate=round(success_rate, 2),
        )
