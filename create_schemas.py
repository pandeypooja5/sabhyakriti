#!/usr/bin/env python3
"""Create missing database schemas for Sabhyakriti services."""

import asyncio
import os
from sqlalchemy import text, create_engine

async def create_schemas():
    """Create missing schemas in PostgreSQL."""
    # Get DATABASE_URL from environment or use the one from context
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:LKgNkLqZYuDyKbaPYvphtrEqZcPUIblE@postgres.railway.internal:5432/railway')

    # Convert to sync connection for schema creation
    sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://').replace('postgresql://', 'postgresql://')

    try:
        engine = create_engine(sync_url, echo=False)
        with engine.connect() as conn:
            schemas = ['product', 'cart', 'orders', 'payment', 'notification']

            for schema in schemas:
                try:
                    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
                    print(f"✓ Created schema: {schema}")
                except Exception as e:
                    print(f"✗ Error creating schema {schema}: {e}")

            # Commit the changes
            conn.commit()

            # Verify schemas
            result = conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('product', 'cart', 'orders', 'payment', 'notification') "
                "ORDER BY schema_name"
            ))

            print("\nVerified schemas:")
            for row in result:
                print(f"  - {row[0]}")

    except Exception as e:
        print(f"Connection error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(create_schemas())
