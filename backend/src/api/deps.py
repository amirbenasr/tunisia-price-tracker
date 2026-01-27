"""API dependencies for dependency injection."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.redis import CacheService, get_redis
from src.core.security import hash_api_key
from src.models import ApiKey
from src.services import (
    PriceService,
    ProductService,
    ScraperService,
    SearchService,
    WebsiteService,
)

from sqlalchemy import select


# Database session dependency
async def get_db_session() -> AsyncSession:
    """Get database session."""
    async for session in get_db():
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db_session)]


# Service dependencies
async def get_search_service(db: DBSession) -> SearchService:
    """Get search service instance."""
    return SearchService(db)


async def get_product_service(db: DBSession) -> ProductService:
    """Get product service instance."""
    return ProductService(db)


async def get_price_service(db: DBSession) -> PriceService:
    """Get price service instance."""
    return PriceService(db)


async def get_website_service(db: DBSession) -> WebsiteService:
    """Get website service instance."""
    return WebsiteService(db)


async def get_scraper_service(db: DBSession) -> ScraperService:
    """Get scraper service instance."""
    return ScraperService(db)


async def get_cache_service() -> CacheService:
    """Get cache service instance."""
    redis = await get_redis()
    return CacheService(redis)


# Type aliases for cleaner dependency injection
SearchSvc = Annotated[SearchService, Depends(get_search_service)]
ProductSvc = Annotated[ProductService, Depends(get_product_service)]
PriceSvc = Annotated[PriceService, Depends(get_price_service)]
WebsiteSvc = Annotated[WebsiteService, Depends(get_website_service)]
ScraperSvc = Annotated[ScraperService, Depends(get_scraper_service)]
CacheSvc = Annotated[CacheService, Depends(get_cache_service)]


# API Key authentication
async def verify_api_key(
    db: DBSession,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[ApiKey]:
    """
    Verify API key from header.

    Returns None if no key provided (for public endpoints).
    Raises 401 if key is invalid.
    """
    if not x_api_key:
        return None

    key_hash = hash_api_key(x_api_key)
    stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive",
        )

    return api_key


async def require_api_key(
    api_key: Optional[ApiKey] = Depends(verify_api_key),
) -> ApiKey:
    """Require valid API key for protected endpoints."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return api_key


# Permission checking
def require_permission(permission: str):
    """Create a dependency that checks for a specific permission."""

    async def check_permission(
        api_key: ApiKey = Depends(require_api_key),
    ) -> ApiKey:
        permissions = api_key.permissions or {}

        # Parse permission path like "products.write"
        parts = permission.split(".")
        value = permissions

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, False)
            else:
                break

        if not value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )

        return api_key

    return check_permission


# Rate limiting
async def check_rate_limit(
    cache: CacheSvc,
    api_key: Optional[ApiKey] = Depends(verify_api_key),
) -> None:
    """Check rate limit for the request."""
    if not api_key:
        # Default rate limit for unauthenticated requests
        key = "ratelimit:anonymous"
        limit = 30  # requests per minute
    else:
        key = f"ratelimit:{api_key.id}"
        limit = api_key.rate_limit

    current = await cache.increment(key, ttl=60)

    if current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
