"""
Test configuration and fixtures.
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.db import Base
from app.deps import get_session
from app.main import app


# PostgreSQL test database URL
# Use environment variable or default to test database on port 5433
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5433/test_db"
)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        poolclass=None  # Disable pooling for tests to avoid connection issues
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_session):
    """Create an async test client with dependency overrides."""
    
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session
    
    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session
    
    # Use AsyncClient with ASGITransport for proper async testing
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

