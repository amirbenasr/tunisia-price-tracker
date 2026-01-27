"""Website API endpoints for managing competitor sites."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import WebsiteSvc
from src.schemas.common import MessageResponse, PaginatedResponse
from src.schemas.website import (
    WebsiteCreate,
    WebsiteListResponse,
    WebsiteResponse,
    WebsiteStats,
    WebsiteUpdate,
)

router = APIRouter(prefix="/websites", tags=["Websites"])


@router.get("", response_model=PaginatedResponse[WebsiteListResponse])
async def list_websites(
    website_service: WebsiteSvc,
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
):
    """
    List all tracked competitor websites.

    Returns basic information about each website including
    product count and last scrape timestamp.
    """
    offset = (page - 1) * page_size
    websites, total = await website_service.get_websites(
        is_active=is_active,
        offset=offset,
        limit=page_size,
    )

    items = [
        WebsiteListResponse(
            id=w.id,
            name=w.name,
            base_url=w.base_url,
            logo_url=w.logo_url,
            is_active=w.is_active,
            total_products=w.total_products,
            last_scraped_at=w.last_scraped_at,
        )
        for w in websites
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: UUID,
    website_service: WebsiteSvc,
):
    """Get detailed information about a specific website."""
    website = await website_service.get_website(website_id)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website {website_id} not found",
        )
    return WebsiteResponse.model_validate(website)


@router.get("/{website_id}/stats", response_model=WebsiteStats)
async def get_website_stats(
    website_id: UUID,
    website_service: WebsiteSvc,
):
    """
    Get detailed statistics for a website.

    Includes product counts, price record totals, scrape success rates,
    and other analytics useful for monitoring scraper health.
    """
    stats = await website_service.get_website_stats(website_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website {website_id} not found",
        )
    return stats


@router.post("", response_model=WebsiteResponse, status_code=status.HTTP_201_CREATED)
async def create_website(
    data: WebsiteCreate,
    website_service: WebsiteSvc,
):
    """
    Add a new competitor website to track.

    After creating a website, you'll need to configure its
    scraper selectors before running scrapes.
    """
    existing = await website_service.get_website_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Website with name '{data.name}' already exists",
        )

    website = await website_service.create_website(data)
    return WebsiteResponse.model_validate(website)


@router.put("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: UUID,
    data: WebsiteUpdate,
    website_service: WebsiteSvc,
):
    """Update a website's configuration."""
    website = await website_service.update_website(website_id, data)
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website {website_id} not found",
        )
    return WebsiteResponse.model_validate(website)


@router.delete("/{website_id}", response_model=MessageResponse)
async def delete_website(
    website_id: UUID,
    website_service: WebsiteSvc,
):
    """
    Delete a website and all its associated data.

    This will remove all products, price records, scraper configs,
    and scrape logs for this website. This action cannot be undone.
    """
    deleted = await website_service.delete_website(website_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website {website_id} not found",
        )
    return MessageResponse(message=f"Website {website_id} deleted successfully")
