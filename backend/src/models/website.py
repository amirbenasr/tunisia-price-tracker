"""Website model for competitor sites."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.product import Product
    from src.models.scraper_config import ScraperConfig
    from src.models.scrape_log import ScrapeLog


class Website(BaseModel):
    """Model representing a competitor website to scrape."""

    __tablename__ = "websites"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Scraper configuration
    scraper_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="config_driven"
    )  # 'config_driven' or 'custom'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rate_limit_ms: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)

    # Tracking
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_products: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="website", cascade="all, delete-orphan"
    )
    scraper_configs: Mapped[List["ScraperConfig"]] = relationship(
        "ScraperConfig", back_populates="website", cascade="all, delete-orphan"
    )
    scrape_logs: Mapped[List["ScrapeLog"]] = relationship(
        "ScrapeLog", back_populates="website", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Website(name='{self.name}', url='{self.base_url}')>"
