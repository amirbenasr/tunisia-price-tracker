"""Website schemas for API requests and responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, HttpUrl

from src.schemas.common import BaseSchema, IDSchema, TimestampSchema


class WebsiteBase(BaseSchema):
    """Base website schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Website name")
    base_url: str = Field(..., max_length=500, description="Base URL of the website")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    description: Optional[str] = Field(None, description="Website description")
    scraper_type: str = Field(
        default="config_driven",
        description="Scraper type: 'config_driven' or 'custom'",
    )
    is_active: bool = Field(default=True, description="Whether scraping is active")
    rate_limit_ms: int = Field(
        default=1000, ge=100, le=60000, description="Rate limit in milliseconds"
    )


class WebsiteCreate(WebsiteBase):
    """Schema for creating a website."""

    pass


class WebsiteUpdate(BaseSchema):
    """Schema for updating a website."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    scraper_type: Optional[str] = None
    is_active: Optional[bool] = None
    rate_limit_ms: Optional[int] = Field(None, ge=100, le=60000)


class WebsiteResponse(WebsiteBase, IDSchema, TimestampSchema):
    """Website response schema."""

    last_scraped_at: Optional[datetime] = None
    total_products: int = 0


class WebsiteListResponse(BaseSchema):
    """Website list item (lighter than full response)."""

    id: UUID
    name: str
    base_url: str
    logo_url: Optional[str] = None
    is_active: bool
    total_products: int
    last_scraped_at: Optional[datetime] = None


class WebsiteStats(BaseSchema):
    """Website statistics."""

    total_products: int
    active_products: int
    total_price_records: int
    last_scraped_at: Optional[datetime]
    avg_products_per_scrape: float
    scrape_success_rate: float
