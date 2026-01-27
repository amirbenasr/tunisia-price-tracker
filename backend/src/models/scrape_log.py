"""Scrape log model for tracking scraping job results."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.website import Website


class ScrapeLog(BaseModel):
    """Model for logging scraping job results."""

    __tablename__ = "scrape_logs"

    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False, index=True
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status: 'running', 'success', 'partial', 'failed'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")

    # Statistics
    products_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    products_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    products_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prices_recorded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_scraped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error tracking
    errors: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        comment="List of errors encountered during scrape",
    )

    # Metadata
    triggered_by: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'schedule', 'manual', 'api'
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    website: Mapped["Website"] = relationship("Website", back_populates="scrape_logs")

    def __repr__(self) -> str:
        return f"<ScrapeLog(website_id='{self.website_id}', status='{self.status}')>"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate scrape duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
