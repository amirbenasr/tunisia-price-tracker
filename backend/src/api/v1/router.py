"""API v1 router aggregating all endpoint modules."""

from fastapi import APIRouter

from src.api.v1.prices import router as prices_router
from src.api.v1.products import router as products_router
from src.api.v1.scrapers import router as scrapers_router
from src.api.v1.search import router as search_router
from src.api.v1.stats import router as stats_router
from src.api.v1.websites import router as websites_router

api_router = APIRouter()

# Include all routers
api_router.include_router(search_router)  # Core search functionality
api_router.include_router(products_router)
api_router.include_router(prices_router)
api_router.include_router(websites_router)
api_router.include_router(scrapers_router)
api_router.include_router(stats_router)
