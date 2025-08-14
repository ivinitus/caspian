#!/usr/bin/env python
import asyncio
from app.db.models import init_db

async def setup_database():
    await init_db()
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(setup_database())
