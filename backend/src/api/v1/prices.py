"""Price API endpoints for history and analytics."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import PriceSvc
from src.schemas.price import (
    PriceDropResponse,
    PriceHistoryResponse,
    PriceTrendResponse,
)

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get("/history/{product_id}", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: UUID,
    price_service: PriceSvc,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
):
    """
    Get price history for a specific product.

    Returns historical price records along with statistics like
    min, max, and average prices over the period.

    The data can be used to plot price charts or analyze trends.
    """
    try:
        return await price_service.get_price_history(
            product_id=product_id,
            days=days,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/trend/{product_id}", response_model=PriceTrendResponse)
async def get_price_trend(
    product_id: UUID,
    price_service: PriceSvc,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get price trend analysis for a product.

    Returns analysis including:
    - Start and end prices
    - Price change amount and percentage
    - Min, max, and average prices
    - Data points for charting
    """
    try:
        return await price_service.get_price_trend(
            product_id=product_id,
            days=days,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/drops", response_model=List[PriceDropResponse])
async def get_price_drops(
    price_service: PriceSvc,
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
    min_drop_percentage: float = Query(default=5.0, ge=1, le=90, description="Minimum drop %"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
):
    """
    Get recent price drops across all products.

    Returns products that have had price drops within the specified
    time window, sorted by drop percentage (largest first).

    Useful for finding deals or tracking competitor pricing strategies.
    """
    return await price_service.get_recent_price_drops(
        hours=hours,
        min_drop_percentage=min_drop_percentage,
        limit=limit,
    )
