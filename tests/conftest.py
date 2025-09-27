import os

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app

# Test database URL - use SQLite for local testing, PostgreSQL for CI
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Create test engine
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test Redis client - use a mock for local testing if Redis is not available
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
try:
    test_redis = redis.from_url(redis_url, decode_responses=True)
    # Test connection
    test_redis.ping()
except Exception:
    # If Redis is not available, create a mock
    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex=None):
            self.data[key] = value

        def setex(self, key, time, value):
            self.data[key] = value

        def incr(self, key, amount=1):
            current = int(self.data.get(key, 0))
            new_value = current + amount
            self.data[key] = str(new_value)
            return new_value

        def delete(self, key):
            self.data.pop(key, None)

        def flushdb(self):
            self.data.clear()

        def ping(self):
            return True

    test_redis = MockRedis()


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def setup_database():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    """Create a test database session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override"""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app.auth import get_password_hash
    from app.models import User

    user = User(username="testuser", hashed_password=get_password_hash("testpass"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    """Get admin authentication headers"""
    # Seed admin user
    client.post("/auth/seed")

    response = client.post(
        "/auth/login", json={"username": "admin", "password": "admin"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def cleanup_redis():
    """Clean up Redis after each test"""
    yield
    test_redis.flushdb()
