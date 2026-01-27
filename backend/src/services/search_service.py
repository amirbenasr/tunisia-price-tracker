"""Search service implementing fuzzy product search across all competitors."""

import time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PriceRecord, Product, Website
from src.schemas.search import (
    SearchQuery,
    SearchResponse,
    SearchResultItem,
    SearchSuggestion,
    SearchSuggestionsResponse,
)


class SearchService:
    """Service for searching products across all competitor websites."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_prices(self, query: SearchQuery) -> SearchResponse:
        """
        Search for products matching the query and return all competitor prices.

        Uses PostgreSQL pg_trgm for fuzzy matching and full-text search
        for keyword matching. Results are ranked by match score.
        """
        start_time = time.time()

        # Build the search query using trigram similarity and full-text search
        # Using similarity() from pg_trgm extension
        similarity_col = func.similarity(Product.name, query.q).label("match_score")

        # Subquery to get the latest price for each product
        latest_price_subq = (
            select(
                PriceRecord.product_id,
                PriceRecord.price,
                PriceRecord.original_price,
                PriceRecord.currency,
                PriceRecord.in_stock,
                PriceRecord.recorded_at,
            )
            .distinct(PriceRecord.product_id)
            .order_by(PriceRecord.product_id, PriceRecord.recorded_at.desc())
            .subquery()
        )

        # Main query joining products, websites, and latest prices
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.brand,
                Product.product_url,
                Product.image_url,
                Website.id.label("website_id"),
                Website.name.label("website_name"),
                Website.logo_url.label("website_logo"),
                latest_price_subq.c.price,
                latest_price_subq.c.original_price,
                latest_price_subq.c.currency,
                latest_price_subq.c.in_stock,
                latest_price_subq.c.recorded_at.label("last_updated"),
                similarity_col,
            )
            .join(Website, Product.website_id == Website.id)
            .join(
                latest_price_subq,
                Product.id == latest_price_subq.c.product_id,
                isouter=True,
            )
            .where(
                and_(
                    Product.is_active == True,
                    Website.is_active == True,
                    # Fuzzy match using trigram similarity OR full-text search
                    or_(
                        func.similarity(Product.name, query.q) > query.min_score,
                        Product.name.ilike(f"%{query.q}%"),
                    ),
                )
            )
        )

        # Apply optional filters
        if query.brand:
            stmt = stmt.where(Product.brand.ilike(f"%{query.brand}%"))

        if query.min_price is not None:
            stmt = stmt.where(latest_price_subq.c.price >= query.min_price)

        if query.max_price is not None:
            stmt = stmt.where(latest_price_subq.c.price <= query.max_price)

        if query.in_stock_only:
            stmt = stmt.where(latest_price_subq.c.in_stock == True)

        if query.website_ids:
            stmt = stmt.where(Website.id.in_(query.website_ids))

        # Order by match score descending, then by price ascending
        stmt = stmt.order_by(similarity_col.desc(), latest_price_subq.c.price.asc())

        # Apply limit
        stmt = stmt.limit(query.limit)

        # Execute query
        result = await self.db.execute(stmt)
        rows = result.all()

        # Count total websites searched
        websites_count_stmt = select(func.count(Website.id)).where(Website.is_active == True)
        websites_result = await self.db.execute(websites_count_stmt)
        websites_searched = websites_result.scalar() or 0

        # Build response
        results = []
        for row in rows:
            if row.price is not None:  # Only include products with prices
                results.append(
                    SearchResultItem(
                        product_id=row.product_id,
                        product_name=row.product_name,
                        brand=row.brand,
                        website=row.website_name,
                        website_id=row.website_id,
                        website_logo=row.website_logo,
                        price=row.price,
                        original_price=row.original_price,
                        currency=row.currency or "TND",
                        in_stock=row.in_stock if row.in_stock is not None else True,
                        product_url=row.product_url,
                        image_url=row.image_url,
                        last_updated=row.last_updated,
                        match_score=float(row.match_score) if row.match_score else 0.0,
                    )
                )

        search_time_ms = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query.q,
            results=results,
            total_results=len(results),
            websites_searched=websites_searched,
            search_time_ms=round(search_time_ms, 2),
        )

    async def get_suggestions(
        self, query: str, limit: int = 10
    ) -> SearchSuggestionsResponse:
        """
        Get autocomplete suggestions for a partial query.

        Uses trigram similarity to find similar product names.
        """
        # Get distinct product names that match the query
        stmt = (
            select(
                Product.name,
                func.count(Product.id).label("count"),
            )
            .where(
                and_(
                    Product.is_active == True,
                    or_(
                        func.similarity(Product.name, query) > 0.2,
                        Product.name.ilike(f"%{query}%"),
                    ),
                )
            )
            .group_by(Product.name)
            .order_by(func.similarity(Product.name, query).desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        suggestions = [
            SearchSuggestion(text=row.name, count=row.count) for row in rows
        ]

        return SearchSuggestionsResponse(query=query, suggestions=suggestions)

    async def get_product_prices_comparison(
        self, product_name: str, min_score: float = 0.5
    ) -> List[SearchResultItem]:
        """
        Get prices for a specific product across all competitors.

        Uses higher minimum score for more precise matching.
        """
        query = SearchQuery(q=product_name, min_score=min_score, limit=50)
        response = await self.search_prices(query)
        return response.results
