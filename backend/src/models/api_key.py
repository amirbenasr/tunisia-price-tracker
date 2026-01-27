"""API key model for external access management."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel


class ApiKey(BaseModel):
    """Model for managing API keys for external access."""

    __tablename__ = "api_keys"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Key storage (hashed)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # First chars for identification

    # Permissions
    permissions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Permissions granted to this API key",
    )

    # Rate limiting
    rate_limit: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False, comment="Requests per minute"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Usage tracking
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<ApiKey(name='{self.name}', prefix='{self.key_prefix}')>"


# Default permissions structure
DEFAULT_PERMISSIONS = {
    "search": True,  # Can use search endpoints
    "products": {"read": True, "write": False},
    "prices": {"read": True},
    "websites": {"read": True, "write": False},
    "scrapers": {"read": False, "write": False, "trigger": False},
}

ADMIN_PERMISSIONS = {
    "search": True,
    "products": {"read": True, "write": True},
    "prices": {"read": True, "write": True},
    "websites": {"read": True, "write": True},
    "scrapers": {"read": True, "write": True, "trigger": True},
}
