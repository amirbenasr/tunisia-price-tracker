"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app

# Test database URL - use a separate test database
TEST_DATABASE_URL = "postgresql+asyncpg://tracker:tracker_dev_password@localhost:5432/tunisia_tracker_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_website_data():
    """Sample website data for tests."""
    return {
        "name": f"Test Website {uuid4().hex[:8]}",
        "base_url": "https://example.com",
        "scraper_type": "config_driven",
        "is_active": True,
        "rate_limit_ms": 1000,
    }


@pytest.fixture
def sample_scraper_config():
    """Sample scraper configuration for tests."""
    return {
        "selectors": {
            "container": ".products",
            "item": ".product-item",
            "name": ".product-name",
            "price": ".product-price",
            "url": "a.product-link::attr(href)",
            "image": "img.product-image::attr(src)",
        },
        "pagination_config": {
            "type": "next_button",
            "next_selector": ".pagination .next::attr(href)",
            "max_pages": 10,
        },
    }
