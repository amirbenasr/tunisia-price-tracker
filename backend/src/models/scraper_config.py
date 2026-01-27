"""Scraper configuration model for storing website-specific scraping selectors."""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.website import Website


class ScraperConfig(BaseModel):
    """
    Model for storing scraper configuration.

    Stores CSS/XPath selectors and pagination config for config-driven scrapers.
    """

    __tablename__ = "scraper_configs"

    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False, index=True
    )

    # Config type: 'product_list', 'product_detail', 'category_list', etc.
    config_type: Mapped[str] = mapped_column(String(50), nullable=False, default="product_list")

    # CSS/XPath selectors stored as JSON
    selectors: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="CSS/XPath selectors for extracting data",
    )

    # Pagination configuration
    pagination_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Pagination strategy and selectors",
    )

    # Authentication config if needed
    auth_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Login/auth configuration",
    )

    # Version tracking for config changes
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    website: Mapped["Website"] = relationship("Website", back_populates="scraper_configs")

    def __repr__(self) -> str:
        return f"<ScraperConfig(website_id='{self.website_id}', type='{self.config_type}', v{self.version})>"


# Example selector configuration structure:
SELECTOR_CONFIG_EXAMPLE = {
    "product_list": {
        "selectors": {
            "container": ".product-grid",
            "item": ".product-item",
            "name": ".product-title",
            "price": ".price-current",
            "original_price": ".price-old",
            "image": "img.product-image::attr(src)",
            "url": "a.product-link::attr(href)",
            "in_stock": ".stock-status",
        },
        "pagination_config": {
            "type": "next_button",  # or 'infinite_scroll', 'page_number'
            "next_selector": ".pagination .next::attr(href)",
            "max_pages": 50,
        },
    },
    "product_detail": {
        "selectors": {
            "name": "h1.product-title",
            "description": ".product-description",
            "brand": ".product-brand",
            "sku": ".product-sku",
            "ean": ".product-ean",
            "category": ".breadcrumb li:last-child",
        },
    },
}
