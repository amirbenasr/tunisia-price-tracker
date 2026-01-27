"""Script to generate a new API key."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.core.security import generate_api_key, hash_api_key
from src.models import ApiKey
from src.models.api_key import DEFAULT_PERMISSIONS, ADMIN_PERMISSIONS


async def create_api_key(
    name: str,
    description: str = "",
    admin: bool = False,
    rate_limit: int = 100,
):
    """Create a new API key."""
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    key = generate_api_key()
    permissions = ADMIN_PERMISSIONS if admin else DEFAULT_PERMISSIONS

    async with session_factory() as db:
        api_key = ApiKey(
            name=name,
            description=description,
            key_hash=hash_api_key(key),
            key_prefix=key[:8],
            permissions=permissions,
            rate_limit=rate_limit,
        )
        db.add(api_key)
        await db.commit()

        print(f"\nAPI Key created successfully!")
        print(f"Name: {name}")
        print(f"Type: {'Admin' if admin else 'Standard'}")
        print(f"Rate Limit: {rate_limit} requests/minute")
        print(f"\nAPI Key: {key}")
        print("\n⚠️  Save this key now - it cannot be retrieved later!")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Generate a new API key")
    parser.add_argument("name", help="Name for the API key")
    parser.add_argument("--description", "-d", default="", help="Description")
    parser.add_argument("--admin", "-a", action="store_true", help="Create admin key")
    parser.add_argument("--rate-limit", "-r", type=int, default=100, help="Rate limit per minute")

    args = parser.parse_args()

    asyncio.run(create_api_key(
        name=args.name,
        description=args.description,
        admin=args.admin,
        rate_limit=args.rate_limit,
    ))


if __name__ == "__main__":
    main()
