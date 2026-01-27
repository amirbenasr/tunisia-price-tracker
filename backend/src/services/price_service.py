"""Price service for managing price records and analytics."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PriceRecord, Product, Website
from src.schemas.price import (
    PriceDropResponse,
    PriceHistoryResponse,
    PriceRecordCreate,
    PriceRecordResponse,
    PriceTrendResponse,
)


class PriceService:
    """Service for managing price records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_price(self, data: PriceRecordCreate) -> PriceRecord:
        """Record a new price for a product."""
        price_record = PriceRecord(**data.model_dump())
        self.db.add(price_record)
        await self.db.commit()
        await self.db.refresh(price_record)
        return price_record

    async def record_price_simple(
        self,
        product_id: UUID,
        price: Decimal,
        original_price: Optional[Decimal] = None,
        in_stock: bool = True,
        currency: str = "TND",
    ) -> PriceRecord:
        """Simplified price recording."""
        price_record = PriceRecord(
            product_id=product_id,
            price=price,
            original_price=original_price,
            in_stock=in_stock,
            currency=currency,
        )
        self.db.add(price_record)
        await self.db.commit()
        await self.db.refresh(price_record)
        return price_record

    async def get_latest_price(self, product_id: UUID) -> Optional[PriceRecord]:
        """Get the most recent price record for a product."""
        stmt = (
            select(PriceRecord)
            .where(PriceRecord.product_id == product_id)
            .order_by(PriceRecord.recorded_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_price_history(
        self,
        product_id: UUID,
        days: int = 30,
        limit: int = 100,
    ) -> PriceHistoryResponse:
        """Get price history for a product."""
        # Get product info
        product_stmt = (
            select(Product.name, Website.name.label("website_name"))
            .join(Website, Product.website_id == Website.id)
            .where(Product.id == product_id)
        )
        product_result = await self.db.execute(product_stmt)
        product_info = product_result.first()

        if not product_info:
            raise ValueError(f"Product {product_id} not found")

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get price records
        stmt = (
            select(PriceRecord)
            .where(
                and_(
                    PriceRecord.product_id == product_id,
                    PriceRecord.recorded_at >= start_date,
                )
            )
            .order_by(PriceRecord.recorded_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()

        # Calculate statistics
        prices = [r.price for r in records]
        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
        avg_price = sum(prices) / len(prices) if prices else None
        current_price = prices[0] if prices else None

        return PriceHistoryResponse(
            product_id=product_id,
            product_name=product_info.name,
            website_name=product_info.website_name,
            records=[
                PriceRecordResponse(
                    id=r.id,
                    product_id=r.product_id,
                    price=r.price,
                    original_price=r.original_price,
                    currency=r.currency,
                    in_stock=r.in_stock,
                    recorded_at=r.recorded_at,
                    discount_percentage=r.discount_percentage,
                )
                for r in records
            ],
            min_price=min_price,
            max_price=max_price,
            avg_price=Decimal(str(round(avg_price, 3))) if avg_price else None,
            current_price=current_price,
        )

    async def get_recent_price_drops(
        self,
        hours: int = 24,
        min_drop_percentage: float = 5.0,
        limit: int = 50,
    ) -> List[PriceDropResponse]:
        """Get products with recent price drops."""
        # Get products with price drops by comparing recent prices
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # This is a simplified query - in production you might want to use
        # a more sophisticated approach with window functions
        stmt = """
            WITH recent_prices AS (
                SELECT
                    product_id,
                    price,
                    recorded_at,
                    LAG(price) OVER (PARTITION BY product_id ORDER BY recorded_at) as previous_price
                FROM price_records
                WHERE recorded_at >= :cutoff_time
            )
            SELECT
                p.id as product_id,
                p.name as product_name,
                p.product_url,
                p.image_url,
                w.name as website_name,
                w.logo_url as website_logo,
                rp.previous_price,
                rp.price as current_price,
                (rp.previous_price - rp.price) as drop_amount,
                ((rp.previous_price - rp.price) / rp.previous_price * 100) as drop_percentage,
                rp.recorded_at
            FROM recent_prices rp
            JOIN products p ON rp.product_id = p.id
            JOIN websites w ON p.website_id = w.id
            WHERE rp.previous_price IS NOT NULL
                AND rp.price < rp.previous_price
                AND ((rp.previous_price - rp.price) / rp.previous_price * 100) >= :min_drop
            ORDER BY drop_percentage DESC
            LIMIT :limit
        """

        result = await self.db.execute(
            select("*").from_statement(
                stmt.replace(":cutoff_time", f"'{cutoff_time.isoformat()}'")
                .replace(":min_drop", str(min_drop_percentage))
                .replace(":limit", str(limit))
            )
        )

        # For now, return empty list - this query needs proper raw SQL execution
        # In production, use text() from sqlalchemy
        return []

    async def get_price_trend(
        self,
        product_id: UUID,
        days: int = 30,
    ) -> PriceTrendResponse:
        """Get price trend analysis for a product."""
        history = await self.get_price_history(product_id, days=days)

        if not history.records:
            raise ValueError(f"No price records found for product {product_id}")

        records = history.records
        start_price = records[-1].price  # Oldest
        end_price = records[0].price  # Newest
        price_change = end_price - start_price
        price_change_pct = float((price_change / start_price) * 100) if start_price else 0

        return PriceTrendResponse(
            product_id=product_id,
            product_name=history.product_name,
            website_name=history.website_name,
            currency=history.currency,
            period_start=records[-1].recorded_at,
            period_end=records[0].recorded_at,
            start_price=start_price,
            end_price=end_price,
            min_price=history.min_price,
            max_price=history.max_price,
            avg_price=history.avg_price,
            price_change=price_change,
            price_change_percentage=round(price_change_pct, 2),
            data_points=[
                {"date": r.recorded_at.isoformat(), "price": float(r.price)}
                for r in reversed(records)  # Chronological order
            ],
        )

    async def should_record_price(
        self,
        product_id: UUID,
        new_price: Decimal,
        min_hours: int = 6,
    ) -> bool:
        """
        Check if we should record a new price.

        Avoids recording duplicate prices within the min_hours window.
        """
        latest = await self.get_latest_price(product_id)

        if not latest:
            return True

        # Check if price changed
        if latest.price != new_price:
            return True

        # Check if enough time has passed
        hours_since = (datetime.utcnow() - latest.recorded_at).total_seconds() / 3600
        return hours_since >= min_hours
