import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base


# Test database URL - using PostgreSQL for testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/datagusto_test")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


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
def client(db_session):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENABLE_REGISTRATION"] = "true"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # Clean up
    if "ENABLE_REGISTRATION" in os.environ:
        del os.environ["ENABLE_REGISTRATION"]
    if "JWT_SECRET_KEY" in os.environ:
        del os.environ["JWT_SECRET_KEY"]
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]