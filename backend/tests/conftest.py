import os
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/datagusto_test")
os.environ["ENABLE_REGISTRATION"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_REFRESH_SECRET_KEY"] = "test-refresh-secret-key-for-testing-only"

from app.main import app
from app.core.database import get_db, Base
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


# Test database URL - using PostgreSQL for testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/datagusto_test")
TEST_ASYNC_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Sync engine for backward compatibility
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for future async tests
async_engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False)
AsyncTestingSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


async def get_async_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async test database session."""
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    # Drop and recreate all tables for clean slate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create database session for each test with transaction rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def async_db_session(test_db):
    """Create async database session for each test with transaction rollback."""
    async with async_engine.begin() as connection:
        async_session = AsyncTestingSessionLocal(bind=connection)
        
        yield async_session
        
        await async_session.close()
        await connection.rollback()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return UserCreate(
        name="Test User",
        email="test@example.com", 
        password="testpassword123"
    )


@pytest.fixture
def sample_user_data_alt():
    """Alternative user data for testing."""
    return UserCreate(
        name="Another User",
        email="another@example.com",
        password="anotherpassword123" 
    )


@pytest.fixture
async def test_user(db_session, sample_user_data):
    """Create a test user with organization."""
    user = await AuthService.register_user(sample_user_data, db_session)
    return user


@pytest.fixture
def sample_langfuse_trace_data():
    """Sample Langfuse trace data for testing."""
    return {
        "id": "test-trace-123",
        "name": "test_trace",
        "timestamp": "2024-01-01T10:00:00Z",
        "metadata": {"version": "1.0", "user_id": "user123"},
        "input": {"query": "What is artificial intelligence?"},
        "output": {"response": "Artificial intelligence is a field of computer science."}
    }


@pytest.fixture  
def sample_langfuse_observation_data():
    """Sample Langfuse observation data for testing."""
    return {
        "id": "test-obs-123",
        "startTime": "2024-01-01T10:00:00Z",
        "parentObservationId": None,
        "type": "generation",
        "input": {"prompt": "What is AI?"},
        "output": {"text": "AI is artificial intelligence."},
        "metadata": {"model": "gpt-4", "tokens": 150}
    }


@pytest.fixture
def sample_project_config():
    """Sample project configuration for testing."""
    return {
        "name": "Test Project",
        "platform_type": "langfuse",
        "platform_config": {
            "public_key": "pk_test_123",
            "secret_key": "sk_test_456",
            "url": "https://cloud.langfuse.com"
        }
    }


@pytest.fixture
def incomplete_langfuse_config():
    """Incomplete Langfuse config for error testing."""
    return {
        "public_key": "pk_test_123"
        # Missing secret_key and url
    }


@pytest.fixture
def quality_test_cases():
    """Test cases for data quality analysis."""
    return {
        "high_quality": {
            "trace": {
                "id": "high-quality-trace",
                "timestamp": "2024-01-01T10:00:00Z",
                "input": {"query": "Complete input data"},
                "output": {"response": "Complete output data"},
                "metadata": {"version": "1.0", "user_id": "user123"}
            },
            "observations": [
                {
                    "id": "obs-high-1",
                    "type": "generation",
                    "input": {"prompt": "Complete prompt"},
                    "output": {"text": "Complete response"},
                    "metadata": {"model": "gpt-4", "tokens": 150}
                }
            ]
        },
        "medium_quality": {
            "trace": {
                "id": "medium-quality-trace", 
                "timestamp": "2024-01-01T10:00:00Z",
                "input": {"query": "Partial input"},
                "output": None,  # Missing output
                "metadata": {}   # Empty metadata
            },
            "observations": [
                {
                    "id": "obs-medium-1",
                    "type": "generation",
                    "input": {"prompt": "Partial prompt"},
                    "output": {"text": ""},  # Empty output
                    "metadata": {"model": "gpt-4"}  # Missing tokens
                }
            ]
        },
        "low_quality": {
            "trace": {
                "id": "low-quality-trace",
                "timestamp": "2024-01-01T10:00:00Z", 
                "input": None,     # Missing input
                "output": None,    # Missing output
                "metadata": None   # Missing metadata
            },
            "observations": [
                {
                    "id": "obs-low-1",
                    "type": "generation",
                    "input": None,     # Missing input
                    "output": None,    # Missing output  
                    "metadata": {}     # Empty metadata
                }
            ]
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENABLE_REGISTRATION"] = "true"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["JWT_REFRESH_SECRET_KEY"] = "test-refresh-secret-key-for-testing-only"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["JWT_REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
    yield
    # Clean up
    env_vars = [
        "ENABLE_REGISTRATION", "JWT_SECRET_KEY", "JWT_REFRESH_SECRET_KEY", 
        "DATABASE_URL", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    ]
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]