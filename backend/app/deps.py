from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from .db import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - handles startup and shutdown events."""
    # Startup
    print("Application starting up...")
    yield
    # Shutdown
    print("Application shutting down...")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    session = SessionLocal()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()