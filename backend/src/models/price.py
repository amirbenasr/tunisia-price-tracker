"""Price record model for tracking product prices over time."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.models.product import Product


class PriceRecord(Base):
    """
    Model for storing price history.

    This table is designed to be a TimescaleDB hypertable, partitioned by recorded_at.
    Each record represents a price snapshot for a product at a specific point in time.
    """

    __tablename__ = "price_records"

    # Composite primary key for hypertable compatibility
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )

    # Price information
    price: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    original_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3), nullable=True
    )  # For discounts
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TND")

    # Stock status
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamp - partition key for TimescaleDB
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), primary_key=True
    )

    # Relationship
    product: Mapped["Product"] = relationship("Product", back_populates="price_records")

    __table_args__ = (
        Index("ix_price_records_product_time", "product_id", "recorded_at"),
        Index("ix_price_records_recorded_at", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<PriceRecord(product_id='{self.product_id}', price={self.price}, recorded_at='{self.recorded_at}')>"

    @property
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage if original price exists."""
        if self.original_price and self.original_price > self.price:
            return float((1 - self.price / self.original_price) * 100)
        return None
