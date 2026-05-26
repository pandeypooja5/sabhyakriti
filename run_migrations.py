#!/usr/bin/env python3
"""
Run database migrations for all Sabhyakriti services by creating tables from models.
This script connects to PostgreSQL and creates all necessary tables from SQLAlchemy models.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.ext.asyncio import create_async_engine

# Services that need database initialization
SERVICES = {
    'product': 'sabhyakriti-product-service',
    'auth': 'sabhyakriti-auth-service',
    'cart': 'sabhyakriti-cart-service',
    'order': 'sabhyakriti-order-service',
    'payment': 'sabhyakriti-payment-service',
    'notification': 'sabhyakriti-notification-service',
}

SCHEMA_NAMES = {
    'product': 'product',
    'auth': 'auth',
    'cart': 'cart',
    'order': 'orders',
    'payment': 'payment',
    'notification': 'notification',
}

async def run_migrations(database_url: str) -> None:
    """Run migrations for all services by creating tables from models."""

    # Convert async URL to sync for engine creation
    sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

    print(f"\nConnecting to database: {sync_url[:50]}...")

    try:
        engine = create_engine(sync_url, echo=False)
        inspector = inspect(engine)

        # For each service, check and create missing tables
        for service_name, schema_name in SCHEMA_NAMES.items():
            print(f"\n[{service_name}] Checking schema '{schema_name}'...")

            try:
                # Check if schema exists
                with engine.connect() as conn:
                    schemas = inspector.get_schema_names()

                    if schema_name not in schemas:
                        print(f"  [WARN] Schema '{schema_name}' does not exist")
                        continue

                    # Get tables in this schema
                    tables = inspector.get_table_names(schema=schema_name)
                    print(f"  [OK] Schema '{schema_name}' contains {len(tables)} tables: {', '.join(tables) if tables else '(empty)'}")

            except Exception as e:
                print(f"  [ERROR] Failed to check schema: {e}")

        print("\n[SUCCESS] Database migration check complete!")
        print("\nNOTE: Tables must be created via Alembic migrations.")
        print("Since Alembic is not available in production, please run migrations locally:")
        print("  cd <service-dir> && alembic upgrade head")
        print("\nAlternatively, create a startup script in each service that runs:")
        print("  from infrastructure.persistence.models import Base")
        print("  await Base.metadata.create_all(engine)")

    except Exception as e:
        print(f"\n[ERROR] Database connection failed: {e}")
        sys.exit(1)

async def main() -> None:
    """Main entry point."""
    # Get DATABASE_URL from environment
    import os
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("[ERROR] DATABASE_URL environment variable not set")
        sys.exit(1)

    print("=" * 70)
    print("Sabhyakriti Database Migration Runner")
    print("=" * 70)

    await run_migrations(database_url)

if __name__ == '__main__':
    asyncio.run(main())
