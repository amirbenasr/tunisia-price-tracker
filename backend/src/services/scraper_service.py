"""Scraper service for managing scraper configurations and jobs."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ScrapeLog, ScraperConfig, Website
from src.schemas.scraper import (
    ScraperConfigCreate,
    ScraperConfigResponse,
    ScraperConfigUpdate,
    ScrapeLogResponse,
)


class ScraperService:
    """Service for managing scraper configurations and logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Scraper Config Methods

    async def get_config(
        self, website_id: UUID, config_type: str = "product_list"
    ) -> Optional[ScraperConfig]:
        """Get active scraper config for a website."""
        stmt = select(ScraperConfig).where(
            and_(
                ScraperConfig.website_id == website_id,
                ScraperConfig.config_type == config_type,
                ScraperConfig.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_configs(self, website_id: UUID) -> List[ScraperConfig]:
        """Get all scraper configs for a website."""
        stmt = (
            select(ScraperConfig)
            .where(ScraperConfig.website_id == website_id)
            .order_by(ScraperConfig.config_type)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_config(self, data: ScraperConfigCreate) -> ScraperConfig:
        """Create a new scraper config."""
        config = ScraperConfig(**data.model_dump())
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update_config(
        self, config_id: UUID, data: ScraperConfigUpdate
    ) -> Optional[ScraperConfig]:
        """Update a scraper config."""
        stmt = select(ScraperConfig).where(ScraperConfig.id == config_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Increment version on any update
        update_data["version"] = config.version + 1

        for field, value in update_data.items():
            setattr(config, field, value)

        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def upsert_config(
        self,
        website_id: UUID,
        config_type: str,
        selectors: Dict[str, Any],
        pagination_config: Optional[Dict[str, Any]] = None,
    ) -> ScraperConfig:
        """Create or update a scraper config."""
        config = await self.get_config(website_id, config_type)

        if config:
            config.selectors = selectors
            config.pagination_config = pagination_config
            config.version += 1
            await self.db.commit()
            await self.db.refresh(config)
        else:
            config = ScraperConfig(
                website_id=website_id,
                config_type=config_type,
                selectors=selectors,
                pagination_config=pagination_config,
            )
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)

        return config

    # Scrape Log Methods

    async def create_log(
        self, website_id: UUID, triggered_by: str = "manual"
    ) -> ScrapeLog:
        """Create a new scrape log entry."""
        log = ScrapeLog(
            website_id=website_id,
            started_at=datetime.utcnow(),
            triggered_by=triggered_by,
            status="running",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def update_log(
        self,
        log_id: UUID,
        status: Optional[str] = None,
        products_found: int = 0,
        products_created: int = 0,
        products_updated: int = 0,
        prices_recorded: int = 0,
        pages_scraped: int = 0,
        errors: Optional[List[Dict[str, Any]]] = None,
        celery_task_id: Optional[str] = None,
    ) -> Optional[ScrapeLog]:
        """Update a scrape log with results."""
        stmt = select(ScrapeLog).where(ScrapeLog.id == log_id)
        result = await self.db.execute(stmt)
        log = result.scalar_one_or_none()

        if not log:
            return None

        if status is not None:
            log.status = status
        if celery_task_id is not None:
            log.celery_task_id = celery_task_id
        if status in ("success", "failed", "partial", "cancelled"):
            log.completed_at = datetime.utcnow()
            log.products_found = products_found
            log.products_created = products_created
            log.products_updated = products_updated
            log.prices_recorded = prices_recorded
            log.pages_scraped = pages_scraped
            log.errors = errors or []
            # Update website last_scraped_at only on completion
            await self.db.execute(
                update(Website)
                .where(Website.id == log.website_id)
                .values(last_scraped_at=datetime.utcnow())
            )

        await self.db.commit()
        await self.db.refresh(log)

        return log

    async def get_logs(
        self,
        website_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ScrapeLog], int]:
        """Get scrape logs with optional filtering."""
        stmt = select(ScrapeLog)

        conditions = []
        if website_id:
            conditions.append(ScrapeLog.website_id == website_id)
        if status:
            conditions.append(ScrapeLog.status == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        from sqlalchemy import func

        count_stmt = select(func.count(ScrapeLog.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(ScrapeLog.started_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        logs = list(result.scalars().all())

        return logs, total

    async def get_latest_log(self, website_id: UUID) -> Optional[ScrapeLog]:
        """Get the most recent scrape log for a website."""
        stmt = (
            select(ScrapeLog)
            .where(ScrapeLog.website_id == website_id)
            .order_by(ScrapeLog.started_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_error_to_log(
        self, log_id: UUID, error: Dict[str, Any]
    ) -> None:
        """Add an error to an existing scrape log."""
        stmt = select(ScrapeLog).where(ScrapeLog.id == log_id)
        result = await self.db.execute(stmt)
        log = result.scalar_one_or_none()

        if log:
            if log.errors is None:
                log.errors = []
            log.errors.append(error)
            await self.db.commit()
