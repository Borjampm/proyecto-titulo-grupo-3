import asyncio
from sqlalchemy import text
from app.db import engine

async def check_version():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT version_num FROM alembic_version'))
        versions = list(result)
        print("Current version in database:")
        for version in versions:
            print(f"  {version[0]}")

if __name__ == "__main__":
    asyncio.run(check_version())
