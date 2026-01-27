"""Product schemas for API requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from src.schemas.common import BaseSchema, IDSchema, TimestampSchema


class ProductBase(BaseSchema):
    """Base product schema."""

    name: str = Field(..., min_length=1, max_length=500, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, max_length=255, description="Product brand")
    product_url: str = Field(..., max_length=1000, description="Product page URL")
    image_url: Optional[str] = Field(None, max_length=1000, description="Product image URL")
    ean_code: Optional[str] = Field(None, max_length=50, description="EAN/Barcode")
    sku: Optional[str] = Field(None, max_length=100, description="SKU")
    external_id: str = Field(..., max_length=255, description="External product ID from website")


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    website_id: UUID
    category_id: Optional[UUID] = None


class ProductUpdate(BaseSchema):
    """Schema for updating a product."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=255)
    product_url: Optional[str] = Field(None, max_length=1000)
    image_url: Optional[str] = Field(None, max_length=1000)
    ean_code: Optional[str] = Field(None, max_length=50)
    sku: Optional[str] = Field(None, max_length=100)
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase, IDSchema, TimestampSchema):
    """Product response schema."""

    website_id: UUID
    category_id: Optional[UUID] = None
    is_active: bool = True


class ProductWithPriceResponse(ProductResponse):
    """Product response with current price info."""

    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    currency: str = "TND"
    in_stock: bool = True
    price_updated_at: Optional[datetime] = None


class ProductListResponse(BaseSchema):
    """Lightweight product list item."""

    id: UUID
    name: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    product_url: str
    website_id: UUID
    website_name: str
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    currency: str = "TND"
    in_stock: bool = True


class ProductSearchResult(BaseSchema):
    """Product search result with match score."""

    id: UUID
    name: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    product_url: str
    website_id: UUID
    website_name: str
    website_logo: Optional[str] = None
    current_price: Decimal
    original_price: Optional[Decimal] = None
    currency: str = "TND"
    in_stock: bool = True
    last_updated: datetime
    match_score: float = Field(..., ge=0, le=1, description="Search match score (0-1)")
