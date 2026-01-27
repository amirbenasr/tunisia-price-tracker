"""Product API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import ProductSvc
from src.schemas.common import PaginatedResponse
from src.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    ProductWithPriceResponse,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse[ProductListResponse])
async def list_products(
    product_service: ProductSvc,
    website_id: Optional[UUID] = Query(default=None, description="Filter by website"),
    category_id: Optional[UUID] = Query(default=None, description="Filter by category"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
):
    """
    List all products with filtering and pagination.

    Products are returned with their current price and basic website info.
    Use filters to narrow down results by website, category, brand, etc.
    """
    offset = (page - 1) * page_size
    products, total = await product_service.get_products(
        website_id=website_id,
        category_id=category_id,
        brand=brand,
        is_active=is_active,
        offset=offset,
        limit=page_size,
    )

    return PaginatedResponse.create(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductWithPriceResponse)
async def get_product(
    product_id: UUID,
    product_service: ProductSvc,
):
    """
    Get detailed information about a specific product.

    Includes the product's current price and price metadata.
    """
    product = await product_service.get_product_with_price(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    product_service: ProductSvc,
):
    """
    Create a new product.

    This endpoint is typically used by scrapers to add products.
    The combination of website_id and external_id must be unique.
    """
    # Check for existing product
    existing = await product_service.get_product_by_external_id(
        data.website_id, data.external_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with external_id '{data.external_id}' already exists for this website",
        )

    product = await product_service.create_product(data)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    product_service: ProductSvc,
):
    """Update an existing product."""
    product = await product_service.update_product(product_id, data)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return ProductResponse.model_validate(product)
