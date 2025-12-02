import asyncio
from sqlalchemy import text
from app.db import engine

async def add_column():
    async with engine.begin() as conn:
        # Add grd_name column
        await conn.execute(text('ALTER TABLE clinical_episodes ADD COLUMN IF NOT EXISTS grd_name VARCHAR(500)'))
        # Update alembic version
        await conn.execute(text("UPDATE alembic_version SET version_num = 'a5b6c7d8e9f0'"))
        print('Added grd_name column and updated alembic version')

if __name__ == "__main__":
    asyncio.run(add_column())
