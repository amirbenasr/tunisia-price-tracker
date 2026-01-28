"""Scraper API endpoints for configuration and job management."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import ScraperSvc
from src.schemas.common import PaginatedResponse
from src.schemas.scraper import (
    ScraperConfigCreate,
    ScraperConfigResponse,
    ScraperConfigUpdate,
    ScrapeJobRequest,
    ScrapeJobResponse,
    ScrapeLogResponse,
)
from workers.tasks.scrape import scrape_website as scrape_website_task
from workers.celery_app import celery_app

router = APIRouter(prefix="/scrapers", tags=["Scrapers"])


# Scraper Configuration Endpoints


@router.get("/{website_id}/config", response_model=List[ScraperConfigResponse])
async def get_scraper_configs(
    website_id: UUID,
    scraper_service: ScraperSvc,
):
    """
    Get all scraper configurations for a website.

    Returns the CSS/XPath selectors and pagination settings
    used to scrape this website.
    """
    configs = await scraper_service.get_all_configs(website_id)
    return [ScraperConfigResponse.model_validate(c) for c in configs]


@router.get("/{website_id}/config/{config_type}", response_model=ScraperConfigResponse)
async def get_scraper_config(
    website_id: UUID,
    config_type: str,
    scraper_service: ScraperSvc,
):
    """Get a specific scraper configuration by type."""
    config = await scraper_service.get_config(website_id, config_type)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {config_type} config found for website {website_id}",
        )
    return ScraperConfigResponse.model_validate(config)


@router.post("/{website_id}/config", response_model=ScraperConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_scraper_config(
    website_id: UUID,
    data: ScraperConfigCreate,
    scraper_service: ScraperSvc,
):
    """
    Create a new scraper configuration.

    Provide CSS selectors for extracting product data from the website.
    The config_type determines what page type this config is for
    (e.g., 'product_list', 'product_detail').

    Example selectors:
    ```json
    {
        "container": ".product-grid",
        "item": ".product-item",
        "name": ".product-title",
        "price": ".price-current",
        "original_price": ".price-old",
        "image": "img.product-image::attr(src)",
        "url": "a.product-link::attr(href)"
    }
    ```
    """
    # Override website_id from path
    data_dict = data.model_dump()
    data_dict["website_id"] = website_id

    config = await scraper_service.create_config(ScraperConfigCreate(**data_dict))
    return ScraperConfigResponse.model_validate(config)


@router.put("/{website_id}/config/{config_id}", response_model=ScraperConfigResponse)
async def update_scraper_config(
    website_id: UUID,
    config_id: UUID,
    data: ScraperConfigUpdate,
    scraper_service: ScraperSvc,
):
    """
    Update a scraper configuration.

    Changes are versioned - each update increments the version number.
    Only provide fields you want to update.
    """
    config = await scraper_service.update_config(config_id, data)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Config {config_id} not found",
        )
    return ScraperConfigResponse.model_validate(config)


# Scrape Job Endpoints


@router.post("/{website_id}/run", response_model=ScrapeJobResponse)
async def trigger_scrape(
    website_id: UUID,
    request: ScrapeJobRequest,
    scraper_service: ScraperSvc,
):
    """
    Trigger a scrape job for a website.

    This queues a background task to scrape the website using
    the configured selectors. The task runs asynchronously.

    Options:
    - full_scrape: Scrape all pages (vs incremental)
    - max_pages: Override the maximum pages to scrape
    - categories: Limit to specific category URLs

    Returns a task_id that can be used to check job status.
    """
    # Create scrape log
    log = await scraper_service.create_log(website_id, triggered_by="api")

    # Dispatch Celery task
    task = scrape_website_task.delay(str(website_id), str(log.id))

    # Update log with Celery task ID
    await scraper_service.update_log(log.id, celery_task_id=task.id, status="running")

    return ScrapeJobResponse(
        task_id=task.id,
        website_id=website_id,
        status="queued",
        message="Scrape job queued successfully. Check /scrapers/{website_id}/logs for status.",
    )


@router.get("/{website_id}/logs", response_model=PaginatedResponse[ScrapeLogResponse])
async def get_scrape_logs(
    website_id: UUID,
    scraper_service: ScraperSvc,
    status: Optional[str] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """
    Get scrape logs for a website.

    Returns the history of scrape jobs including status, timing,
    and statistics (products found, created, updated, etc.).
    """
    offset = (page - 1) * page_size
    logs, total = await scraper_service.get_logs(
        website_id=website_id,
        status=status,
        offset=offset,
        limit=page_size,
    )

    items = [
        ScrapeLogResponse(
            id=log.id,
            website_id=log.website_id,
            started_at=log.started_at,
            completed_at=log.completed_at,
            status=log.status,
            products_found=log.products_found,
            products_created=log.products_created,
            products_updated=log.products_updated,
            prices_recorded=log.prices_recorded,
            pages_scraped=log.pages_scraped,
            errors=log.errors,
            triggered_by=log.triggered_by,
            celery_task_id=log.celery_task_id,
            duration_seconds=log.duration_seconds,
            created_at=log.created_at,
            updated_at=log.updated_at,
        )
        for log in logs
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{website_id}/logs/latest", response_model=ScrapeLogResponse)
async def get_latest_scrape_log(
    website_id: UUID,
    scraper_service: ScraperSvc,
):
    """Get the most recent scrape log for a website."""
    log = await scraper_service.get_latest_log(website_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scrape logs found for website {website_id}",
        )
    return ScrapeLogResponse(
        id=log.id,
        website_id=log.website_id,
        started_at=log.started_at,
        completed_at=log.completed_at,
        status=log.status,
        products_found=log.products_found,
        products_created=log.products_created,
        products_updated=log.products_updated,
        prices_recorded=log.prices_recorded,
        pages_scraped=log.pages_scraped,
        errors=log.errors,
        triggered_by=log.triggered_by,
        celery_task_id=log.celery_task_id,
        duration_seconds=log.duration_seconds,
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


@router.post("/{website_id}/stop", response_model=ScrapeJobResponse)
async def stop_scrape(
    website_id: UUID,
    scraper_service: ScraperSvc,
):
    """
    Stop a running scrape job for a website.

    This will attempt to terminate the running task. The job cannot be resumed
    and will be marked as cancelled.
    """
    # Get the latest running log
    log = await scraper_service.get_latest_log(website_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No scrape logs found for this website",
        )

    if log.status not in ("running", "queued"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop scrape with status '{log.status}'. Only running or queued jobs can be stopped.",
        )

    # Revoke the Celery task
    if log.celery_task_id:
        celery_app.control.revoke(log.celery_task_id, terminate=True, signal="SIGTERM")

    # Update log status to cancelled
    await scraper_service.update_log(log.id, status="cancelled")

    return ScrapeJobResponse(
        task_id=log.celery_task_id or str(log.id),
        website_id=website_id,
        status="cancelled",
        message="Scrape job has been stopped.",
    )
