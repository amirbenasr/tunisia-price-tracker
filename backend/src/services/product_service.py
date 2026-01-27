"""Product service for CRUD operations on products."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import PriceRecord, Product, Website
from src.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    ProductWithPriceResponse,
)


class ProductService:
    """Service for managing products."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """Get a product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product_with_price(
        self, product_id: UUID
    ) -> Optional[ProductWithPriceResponse]:
        """Get a product with its current price."""
        # Subquery for latest price
        latest_price_subq = (
            select(
                PriceRecord.product_id,
                PriceRecord.price,
                PriceRecord.original_price,
                PriceRecord.currency,
                PriceRecord.in_stock,
                PriceRecord.recorded_at,
            )
            .where(PriceRecord.product_id == product_id)
            .order_by(PriceRecord.recorded_at.desc())
            .limit(1)
            .subquery()
        )

        stmt = (
            select(
                Product,
                latest_price_subq.c.price,
                latest_price_subq.c.original_price,
                latest_price_subq.c.currency,
                latest_price_subq.c.in_stock,
                latest_price_subq.c.recorded_at,
            )
            .outerjoin(latest_price_subq, Product.id == latest_price_subq.c.product_id)
            .where(Product.id == product_id)
        )

        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        product = row[0]
        return ProductWithPriceResponse(
            id=product.id,
            website_id=product.website_id,
            category_id=product.category_id,
            external_id=product.external_id,
            name=product.name,
            description=product.description,
            brand=product.brand,
            product_url=product.product_url,
            image_url=product.image_url,
            ean_code=product.ean_code,
            sku=product.sku,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            current_price=row[1],
            original_price=row[2],
            currency=row[3] or "TND",
            in_stock=row[4] if row[4] is not None else True,
            price_updated_at=row[5],
        )

    async def get_products(
        self,
        website_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        brand: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[ProductListResponse], int]:
        """Get products with filtering and pagination."""
        # Base query with latest price
        latest_price_subq = (
            select(
                PriceRecord.product_id,
                PriceRecord.price,
                PriceRecord.original_price,
                PriceRecord.currency,
                PriceRecord.in_stock,
            )
            .distinct(PriceRecord.product_id)
            .order_by(PriceRecord.product_id, PriceRecord.recorded_at.desc())
            .subquery()
        )

        stmt = (
            select(
                Product.id,
                Product.name,
                Product.brand,
                Product.image_url,
                Product.product_url,
                Product.website_id,
                Website.name.label("website_name"),
                latest_price_subq.c.price,
                latest_price_subq.c.original_price,
                latest_price_subq.c.currency,
                latest_price_subq.c.in_stock,
            )
            .join(Website, Product.website_id == Website.id)
            .outerjoin(latest_price_subq, Product.id == latest_price_subq.c.product_id)
        )

        # Apply filters
        conditions = []
        if website_id:
            conditions.append(Product.website_id == website_id)
        if category_id:
            conditions.append(Product.category_id == category_id)
        if brand:
            conditions.append(Product.brand.ilike(f"%{brand}%"))
        if is_active is not None:
            conditions.append(Product.is_active == is_active)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(Product)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Product.updated_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        products = [
            ProductListResponse(
                id=row.id,
                name=row.name,
                brand=row.brand,
                image_url=row.image_url,
                product_url=row.product_url,
                website_id=row.website_id,
                website_name=row.website_name,
                current_price=row.price,
                original_price=row.original_price,
                currency=row.currency or "TND",
                in_stock=row.in_stock if row.in_stock is not None else True,
            )
            for row in rows
        ]

        return products, total

    async def get_product_by_external_id(
        self, website_id: UUID, external_id: str
    ) -> Optional[Product]:
        """Get a product by website and external ID."""
        stmt = select(Product).where(
            and_(Product.website_id == website_id, Product.external_id == external_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_product(self, data: ProductCreate) -> Product:
        """Create a new product."""
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update_product(
        self, product_id: UUID, data: ProductUpdate
    ) -> Optional[Product]:
        """Update an existing product."""
        product = await self.get_product(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def upsert_product(
        self, website_id: UUID, external_id: str, data: dict
    ) -> Tuple[Product, bool]:
        """
        Create or update a product.

        Returns tuple of (product, created) where created is True if new.
        """
        product = await self.get_product_by_external_id(website_id, external_id)

        if product:
            # Update existing
            for field, value in data.items():
                if hasattr(product, field) and value is not None:
                    setattr(product, field, value)
            await self.db.commit()
            await self.db.refresh(product)
            return product, False
        else:
            # Create new
            product = Product(
                website_id=website_id,
                external_id=external_id,
                **data,
            )
            self.db.add(product)
            await self.db.commit()
            await self.db.refresh(product)
            return product, True

    async def deactivate_missing_products(
        self, website_id: UUID, found_external_ids: List[str]
    ) -> int:
        """Mark products not found in scrape as inactive."""
        if not found_external_ids:
            return 0

        stmt = (
            update(Product)
            .where(
                and_(
                    Product.website_id == website_id,
                    Product.external_id.notin_(found_external_ids),
                    Product.is_active == True,
                )
            )
            .values(is_active=False)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
