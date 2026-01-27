"""Pydantic schemas for API requests and responses."""

from src.schemas.common import (
    BaseSchema,
    ErrorResponse,
    HealthResponse,
    IDSchema,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
    TimestampSchema,
)
from src.schemas.price import (
    PriceDropResponse,
    PriceHistoryResponse,
    PriceRecordCreate,
    PriceRecordResponse,
    PriceTrendResponse,
)
from src.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductSearchResult,
    ProductUpdate,
    ProductWithPriceResponse,
)
from src.schemas.scraper import (
    PaginationConfig,
    ScraperConfigCreate,
    ScraperConfigResponse,
    ScraperConfigUpdate,
    ScrapeJobRequest,
    ScrapeJobResponse,
    ScrapeLogResponse,
    SelectorConfig,
)
from src.schemas.search import (
    SearchQuery,
    SearchResponse,
    SearchResultItem,
    SearchSuggestion,
    SearchSuggestionsResponse,
)
from src.schemas.website import (
    WebsiteCreate,
    WebsiteListResponse,
    WebsiteResponse,
    WebsiteStats,
    WebsiteUpdate,
)

__all__ = [
    # Common
    "BaseSchema",
    "IDSchema",
    "TimestampSchema",
    "PaginationParams",
    "PaginatedResponse",
    "MessageResponse",
    "ErrorResponse",
    "HealthResponse",
    # Website
    "WebsiteCreate",
    "WebsiteUpdate",
    "WebsiteResponse",
    "WebsiteListResponse",
    "WebsiteStats",
    # Product
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
    "ProductWithPriceResponse",
    "ProductSearchResult",
    # Price
    "PriceRecordCreate",
    "PriceRecordResponse",
    "PriceHistoryResponse",
    "PriceDropResponse",
    "PriceTrendResponse",
    # Search
    "SearchQuery",
    "SearchResponse",
    "SearchResultItem",
    "SearchSuggestion",
    "SearchSuggestionsResponse",
    # Scraper
    "SelectorConfig",
    "PaginationConfig",
    "ScraperConfigCreate",
    "ScraperConfigUpdate",
    "ScraperConfigResponse",
    "ScrapeJobRequest",
    "ScrapeJobResponse",
    "ScrapeLogResponse",
]
