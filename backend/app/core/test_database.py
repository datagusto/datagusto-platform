"""
Test database configuration module.

This module provides database configuration specifically for testing purposes.
It uses a separate PostgreSQL test database (datagusto_test) and implements
transaction rollback strategy for test isolation.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Test database URL - defaults to datagusto_test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/datagusto_test"
)

# Create test engine with NullPool for better test isolation
# NullPool prevents connection pooling which can interfere with test transactions
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL query debugging
    poolclass=NullPool,  # Disable connection pooling for tests
)

# Create async session factory for tests
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async test database session.

    This dependency function can be used to override get_async_db in tests.
    Each test should use transaction rollback for isolation.

    Yields:
        AsyncSession: Test database session

    Example:
        >>> from app.main import app
        >>> from app.core.database import get_async_db
        >>>
        >>> app.dependency_overrides[get_async_db] = get_test_db
    """
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()