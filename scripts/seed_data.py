"""Script to seed initial data for development/testing."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.config import settings
from src.models import Website, ScraperConfig, Category, ApiKey
from src.core.security import generate_api_key, hash_api_key


async def seed_data():
    """Seed initial data."""
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        print("Seeding initial data...")

        # Create categories
        categories = [
            Category(name="Beauty & Cosmetics", slug="beauty-cosmetics"),
            Category(name="Skincare", slug="skincare"),
            Category(name="Haircare", slug="haircare"),
            Category(name="Makeup", slug="makeup"),
            Category(name="Fragrance", slug="fragrance"),
        ]

        for cat in categories:
            db.add(cat)

        print(f"Created {len(categories)} categories")

        # Create sample websites
        websites_data = [
            {
                "name": "Freya.tn",
                "base_url": "https://freya.tn",
                "description": "Tunisian beauty and cosmetics store",
                "scraper_type": "config_driven",
                "rate_limit_ms": 1500,
            },
            {
                "name": "TunisiaNet",
                "base_url": "https://www.tunisianet.com.tn",
                "description": "Electronics and general merchandise",
                "scraper_type": "config_driven",
                "rate_limit_ms": 2000,
            },
            {
                "name": "MyTek",
                "base_url": "https://www.mytek.tn",
                "description": "Electronics retailer",
                "scraper_type": "config_driven",
                "rate_limit_ms": 2000,
            },
        ]

        for data in websites_data:
            website = Website(**data)
            db.add(website)

        await db.flush()

        print(f"Created {len(websites_data)} websites")

        # Create sample scraper configs
        # These are placeholder selectors - need to be updated with real selectors
        sample_selectors = {
            "container": ".products-grid",
            "item": ".product-item",
            "name": ".product-name, .product-title",
            "price": ".price, .product-price",
            "original_price": ".old-price, .price-old",
            "image": "img.product-image::attr(src)",
            "url": "a.product-link::attr(href), a::attr(href)",
            "in_stock": ".stock-status",
        }

        sample_pagination = {
            "type": "next_button",
            "next_selector": ".pagination .next::attr(href)",
            "max_pages": 50,
        }

        # Get websites to add configs
        from sqlalchemy import select
        result = await db.execute(select(Website))
        websites = result.scalars().all()

        for website in websites:
            config = ScraperConfig(
                website_id=website.id,
                config_type="product_list",
                selectors=sample_selectors,
                pagination_config=sample_pagination,
            )
            db.add(config)

        print(f"Created scraper configs for {len(websites)} websites")

        # Create API keys
        # Admin key
        admin_key = generate_api_key()
        admin_api_key = ApiKey(
            name="Admin API Key",
            description="Full access API key for admin operations",
            key_hash=hash_api_key(admin_key),
            key_prefix=admin_key[:8],
            permissions={
                "search": True,
                "products": {"read": True, "write": True},
                "prices": {"read": True, "write": True},
                "websites": {"read": True, "write": True},
                "scrapers": {"read": True, "write": True, "trigger": True},
            },
            rate_limit=1000,
        )
        db.add(admin_api_key)

        # Public key (limited access)
        public_key = generate_api_key()
        public_api_key = ApiKey(
            name="Public API Key",
            description="Limited access key for public search API",
            key_hash=hash_api_key(public_key),
            key_prefix=public_key[:8],
            permissions={
                "search": True,
                "products": {"read": True, "write": False},
                "prices": {"read": True},
                "websites": {"read": True, "write": False},
                "scrapers": {"read": False, "write": False, "trigger": False},
            },
            rate_limit=100,
        )
        db.add(public_api_key)

        await db.commit()

        print("\nSeeding complete!")
        print("\n=== API Keys ===")
        print(f"Admin API Key: {admin_key}")
        print(f"Public API Key: {public_key}")
        print("\nSave these keys - they cannot be retrieved later!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
