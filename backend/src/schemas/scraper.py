"""Scraper schemas for configuration and job management."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from src.schemas.common import BaseSchema, IDSchema, TimestampSchema


class SelectorConfig(BaseSchema):
    """CSS/XPath selector configuration."""

    container: Optional[str] = Field(None, description="Container element selector")
    item: Optional[str] = Field(None, description="Individual item selector")
    name: Optional[str] = Field(None, description="Product name selector")
    price: Optional[str] = Field(None, description="Current price selector")
    original_price: Optional[str] = Field(None, description="Original price selector")
    image: Optional[str] = Field(None, description="Image selector")
    url: Optional[str] = Field(None, description="Product URL selector")
    in_stock: Optional[str] = Field(None, description="Stock status selector")
    brand: Optional[str] = Field(None, description="Brand selector")
    sku: Optional[str] = Field(None, description="SKU selector")
    description: Optional[str] = Field(None, description="Description selector")


class PaginationConfig(BaseSchema):
    """Pagination configuration."""

    type: str = Field(
        default="next_button",
        description="Pagination type: 'next_button', 'infinite_scroll', 'page_number'",
    )
    next_selector: Optional[str] = Field(None, description="Next page button/link selector")
    page_param: Optional[str] = Field(None, description="URL page parameter name")
    max_pages: int = Field(default=50, ge=1, le=500, description="Maximum pages to scrape")
    wait_ms: int = Field(default=1000, ge=100, description="Wait time between pages")


class SitemapConfig(BaseSchema):
    """Sitemap-based scraper configuration."""

    sitemap_url: str = Field(..., description="URL to the sitemap.xml file")
    child_sitemap_pattern: Optional[str] = Field(
        None,
        description="Regex pattern to filter child sitemaps (e.g., 'sitemap_products' for Shopify)",
    )
    url_include_pattern: Optional[str] = Field(
        None,
        description="Regex pattern - only include URLs matching this (e.g., '/products/')",
    )
    url_exclude_pattern: Optional[str] = Field(
        None,
        description="Regex pattern - exclude URLs matching this (e.g., '/collections|/pages')",
    )
    use_lastmod: bool = Field(
        default=True,
        description="Use lastmod field for incremental scraping",
    )


class ScraperConfigBase(BaseSchema):
    """Base scraper config schema."""

    config_type: str = Field(
        default="product_list",
        description="Config type: 'product_list' (CSS-based) or 'sitemap' (sitemap-based)",
    )
    selectors: Dict[str, Any] = Field(default_factory=dict, description="Selector configuration")
    pagination_config: Optional[Dict[str, Any]] = Field(None, description="Pagination settings")
    sitemap_config: Optional[Dict[str, Any]] = Field(None, description="Sitemap scraper settings")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication settings")
    is_active: bool = Field(default=True)


class ScraperConfigCreate(ScraperConfigBase):
    """Schema for creating scraper config."""

    website_id: UUID


class ScraperConfigUpdate(BaseSchema):
    """Schema for updating scraper config."""

    config_type: Optional[str] = None
    selectors: Optional[Dict[str, Any]] = None
    pagination_config: Optional[Dict[str, Any]] = None
    sitemap_config: Optional[Dict[str, Any]] = None
    auth_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ScraperConfigResponse(ScraperConfigBase, IDSchema, TimestampSchema):
    """Scraper config response."""

    website_id: UUID
    version: int


class ScrapeJobRequest(BaseSchema):
    """Request to trigger a scrape job."""

    full_scrape: bool = Field(default=False, description="Whether to scrape all pages")
    max_pages: Optional[int] = Field(None, ge=1, le=500, description="Override max pages")
    categories: Optional[List[str]] = Field(None, description="Specific categories to scrape")


class ScrapeLogResponse(IDSchema, TimestampSchema):
    """Scrape log response."""

    website_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    products_found: int
    products_created: int
    products_updated: int
    prices_recorded: int
    pages_scraped: int
    errors: Optional[List[Dict[str, Any]]] = None
    triggered_by: Optional[str] = None
    celery_task_id: Optional[str] = None
    duration_seconds: Optional[float] = None


class ScrapeJobResponse(BaseSchema):
    """Response when triggering a scrape job."""

    task_id: str
    website_id: UUID
    status: str = "queued"
    message: str
