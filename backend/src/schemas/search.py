"""Search schemas for the core price search API."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from src.schemas.common import BaseSchema


class SearchQuery(BaseSchema):
    """Search query parameters."""

    q: str = Field(..., min_length=2, max_length=200, description="Search query")
    country: str = Field(default="TN", max_length=2, description="Country code")
    category: Optional[str] = Field(None, description="Category slug filter")
    brand: Optional[str] = Field(None, description="Brand filter")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    in_stock_only: bool = Field(default=False, description="Only show in-stock items")
    min_score: float = Field(default=0.3, ge=0, le=1, description="Minimum match score")
    limit: int = Field(default=20, ge=1, le=100, description="Results limit")
    website_ids: Optional[List[UUID]] = Field(None, description="Filter by specific websites")


class SearchResultItem(BaseSchema):
    """Single search result item."""

    product_id: UUID
    product_name: str = Field(..., description="Product name from the website")
    brand: Optional[str] = None
    website: str = Field(..., description="Website name")
    website_id: UUID
    website_logo: Optional[str] = None
    price: Decimal = Field(..., description="Current price")
    original_price: Optional[Decimal] = Field(None, description="Original price if discounted")
    currency: str = Field(default="TND")
    in_stock: bool = True
    product_url: str = Field(..., description="Direct link to product page")
    image_url: Optional[str] = None
    last_updated: datetime = Field(..., description="When price was last checked")
    match_score: float = Field(..., ge=0, le=1, description="Search relevance score")

    @property
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage."""
        if self.original_price and self.original_price > self.price:
            return float((1 - self.price / self.original_price) * 100)
        return None


class SearchResponse(BaseSchema):
    """Search response containing all competitor prices."""

    query: str = Field(..., description="Original search query")
    results: List[SearchResultItem] = Field(default_factory=list)
    total_results: int = Field(..., description="Total number of matching products")
    websites_searched: int = Field(..., description="Number of websites searched")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")


class SearchSuggestion(BaseSchema):
    """Autocomplete suggestion."""

    text: str = Field(..., description="Suggested search text")
    count: int = Field(..., description="Number of matching products")


class SearchSuggestionsResponse(BaseSchema):
    """Autocomplete suggestions response."""

    query: str
    suggestions: List[SearchSuggestion]
