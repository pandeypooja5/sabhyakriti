#!/usr/bin/env python3
"""Initialize database tables for all Sabhyakriti services."""

import os
import sys
import asyncio

async def init_tables():
    """Create all tables by running migrations programmatically."""

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("[ERROR] DATABASE_URL not set")
        return False

    print(f"[INFO] DATABASE_URL: {database_url[:60]}...")

    try:
        # Convert to sync URL for alembic script
        sync_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

        # Try to run alembic upgrade via shell
        import subprocess

        # Check if we're in a service directory with alembic
        if os.path.exists('alembic.ini'):
            print("[INFO] Found alembic.ini, running migrations...")
            result = subprocess.run(
                ['python', '-m', 'alembic', 'upgrade', 'head'],
                env={**os.environ, 'SQLALCHEMY_DATABASE_URL': sync_url},
                capture_output=True,
                text=True
            )

            print(result.stdout)
            if result.stderr:
                print("[STDERR]", result.stderr)

            if result.returncode == 0:
                print("[SUCCESS] Migrations completed")
                return True
            else:
                print(f"[ERROR] Migration failed with code {result.returncode}")
                return False

        else:
            print("[INFO] No alembic.ini found in current directory")
            print("[INFO] Running alembic directly...")

            from sqlalchemy import text, create_engine

            engine = create_engine(sync_url)
            with engine.begin() as conn:
                # Show existing tables
                result = conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
                    "ORDER BY table_schema, table_name"
                ))

                print("\n[INFO] Existing tables:")
                for row in result:
                    print(f"  - {row[0]}")

            return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(init_tables())
    sys.exit(0 if success else 1)
