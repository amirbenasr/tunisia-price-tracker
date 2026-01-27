"""Product model representing items scraped from competitor websites."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.category import Category
    from src.models.price import PriceRecord
    from src.models.website import Website


class Product(BaseModel):
    """Model representing a product from a competitor website."""

    __tablename__ = "products"

    # Foreign keys
    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False, index=True
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True
    )

    # Product identification - unique per website
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Product details
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # URLs and images
    product_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Additional identifiers
    ean_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    website: Mapped["Website"] = relationship("Website", back_populates="products")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    price_records: Mapped[List["PriceRecord"]] = relationship(
        "PriceRecord", back_populates="product", cascade="all, delete-orphan"
    )

    # Indexes for search and uniqueness
    __table_args__ = (
        Index("ix_products_website_external", "website_id", "external_id", unique=True),
        Index(
            "ix_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_fulltext",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Product(name='{self.name}', website_id='{self.website_id}')>"
