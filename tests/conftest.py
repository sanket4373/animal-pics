import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.storage import get_minio_client, ensure_bucket_exists
from app import storage


# Test database URL - separate from development database
SQLITE_TEST_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine for the entire test session.
    Creates tables at start and drops them at end.
    """
    engine = create_engine(
        SQLITE_TEST_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Teardown: drop all tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Create a fresh database session for each test.
    Ensures test isolation by cleaning tables after each test.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    db = TestingSessionLocal()
    
    yield db
    
    # Teardown: close session and clean all tables
    db.close()
    
    # Clean all tables for next test using connection
    with test_engine.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()


@pytest.fixture
def client(db_session):
    """
    Create a test client with overridden database dependency.
    Uses the test database instead of the real one.
    """
    def override_get_db():
        """Override function that returns test database session."""
        return db_session
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Teardown: clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_minio(monkeypatch):
    """
    Mock MinIO storage with an in-memory dictionary.
    Replaces real storage operations with fake ones for testing.
    """
    # In-memory storage
    store = {}
    
    def fake_put_image(minio_client, object_key, data):
        """Fake put_image that stores in dictionary."""
        store[object_key] = data
    
    def fake_get_image(minio_client, object_key):
        """Fake get_image that retrieves from dictionary."""
        if object_key not in store:
            raise Exception(f"Object {object_key} not found")
        return store[object_key]
    
    def fake_get_minio_client():
        """Fake MinIO client - returns None since mocks don't use it."""
        return None
    
    def fake_ensure_bucket_exists(minio_client):
        """Fake bucket creation - does nothing."""
        pass
    
    # Patch storage functions
    monkeypatch.setattr(storage, "put_image", fake_put_image)
    monkeypatch.setattr(storage, "get_image", fake_get_image)
    monkeypatch.setattr(storage, "get_minio_client", fake_get_minio_client)
    monkeypatch.setattr(storage, "ensure_bucket_exists", fake_ensure_bucket_exists)
    
    yield store  # Return the store so tests can inspect it if needed

# Made with Bob
