#!/usr/bin/env python
import asyncio
from app.db.models import init_db, Base, engine

async def setup_database():
    """
    Drops all existing tables and creates a fresh schema.
    This ensures the database matches the current models.
    """
    print("Connecting to the database to reset schema...")
    async with engine.begin() as conn:
        print("Dropping all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Tables dropped.")

    await init_db()
    print("Database tables created successfully!")
    print("Schema reset is complete.")

if __name__ == "__main__":
    asyncio.run(setup_database())