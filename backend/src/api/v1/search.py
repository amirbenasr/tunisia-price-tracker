"""Search API endpoints - Core functionality for price comparison."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query

from src.api.deps import SearchSvc
from src.schemas.search import SearchQuery, SearchResponse, SearchSuggestionsResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/prices", response_model=SearchResponse)
async def search_prices(
    search_service: SearchSvc,
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    country: str = Query(default="TN", max_length=2, description="Country code"),
    category: Optional[str] = Query(default=None, description="Category slug filter"),
    brand: Optional[str] = Query(default=None, description="Brand filter"),
    min_price: Optional[float] = Query(default=None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, ge=0, description="Maximum price"),
    in_stock_only: bool = Query(default=False, description="Only show in-stock items"),
    min_score: float = Query(default=0.3, ge=0, le=1, description="Minimum match score"),
    limit: int = Query(default=20, ge=1, le=100, description="Results limit"),
    website_ids: Optional[List[UUID]] = Query(default=None, description="Filter by websites"),
):
    """
    Search for products and get all competitor prices.

    This is the primary API endpoint. Provide a product name and get back
    all matching products from all tracked competitor websites, with their
    current prices, sorted by relevance.

    The search uses fuzzy matching (pg_trgm) so it handles:
    - Typos: "anua peech" matches "Anua Peach"
    - Partial matches: "niacinamide serum" matches full product names
    - Different word orders

    Results include:
    - Product name as listed on each website
    - Current price and original price (if discounted)
    - Stock availability
    - Direct link to the product page
    - Match score (0-1) indicating relevance

    Example:
    ```
    GET /api/v1/search/prices?q=anua peach 70% niacin serum
    ```
    """
    from decimal import Decimal

    query = SearchQuery(
        q=q,
        country=country,
        category=category,
        brand=brand,
        min_price=Decimal(str(min_price)) if min_price else None,
        max_price=Decimal(str(max_price)) if max_price else None,
        in_stock_only=in_stock_only,
        min_score=min_score,
        limit=limit,
        website_ids=website_ids,
    )

    return await search_service.search_prices(query)


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_suggestions(
    search_service: SearchSvc,
    q: str = Query(..., min_length=2, max_length=100, description="Partial search query"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of suggestions"),
):
    """
    Get autocomplete suggestions for a partial query.

    Use this for implementing search-as-you-type functionality.
    Returns product names that match the partial query, along with
    the count of products with that name.

    Example:
    ```
    GET /api/v1/search/suggestions?q=anua
    ```
    """
    return await search_service.get_suggestions(q, limit=limit)
