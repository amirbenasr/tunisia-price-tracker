"""Price schemas for API requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from src.schemas.common import BaseSchema


class PriceRecordBase(BaseSchema):
    """Base price record schema."""

    price: Decimal = Field(..., ge=0, description="Current price")
    original_price: Optional[Decimal] = Field(None, ge=0, description="Original price (for discounts)")
    currency: str = Field(default="TND", max_length=3, description="Currency code")
    in_stock: bool = Field(default=True, description="Stock availability")


class PriceRecordCreate(PriceRecordBase):
    """Schema for creating a price record."""

    product_id: UUID


class PriceRecordResponse(PriceRecordBase):
    """Price record response schema."""

    id: UUID
    product_id: UUID
    recorded_at: datetime
    discount_percentage: Optional[float] = None


class PriceHistoryResponse(BaseSchema):
    """Price history for a product."""

    product_id: UUID
    product_name: str
    website_name: str
    currency: str = "TND"
    records: List[PriceRecordResponse]
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    avg_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None


class PriceDropResponse(BaseSchema):
    """Price drop notification."""

    product_id: UUID
    product_name: str
    product_url: str
    image_url: Optional[str] = None
    website_name: str
    website_logo: Optional[str] = None
    previous_price: Decimal
    current_price: Decimal
    drop_amount: Decimal
    drop_percentage: float
    currency: str = "TND"
    recorded_at: datetime


class PriceTrendResponse(BaseSchema):
    """Price trend analysis."""

    product_id: UUID
    product_name: str
    website_name: str
    currency: str = "TND"
    period_start: datetime
    period_end: datetime
    start_price: Decimal
    end_price: Decimal
    min_price: Decimal
    max_price: Decimal
    avg_price: Decimal
    price_change: Decimal
    price_change_percentage: float
    data_points: List[dict]  # [{date: ..., price: ...}]
