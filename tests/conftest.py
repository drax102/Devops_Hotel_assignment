from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import DATABASE_URL, Base, get_db
from app.main import app

# Use DATABASE_URL from environment
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure tables exist before running test suite."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """Provide a clean database session per test function."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI TestClient with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_room(db_session):
    """Fixture providing a fresh test room."""
    import secrets

    unique_num = f"T{secrets.token_hex(3).upper()}"
    room = models.Room(
        room_number=unique_num, room_type="Standard", price_per_night=120
    )
    db_session.add(room)
    db_session.commit()
    db_session.refresh(room)
    return room


@pytest.fixture
def relative_dates():
    """Helper providing test dates relative to today."""
    today = date.today()
    return {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "in_5_days": today + timedelta(days=5),
        "in_10_days": today + timedelta(days=10),
        "in_15_days": today + timedelta(days=15),
        "in_20_days": today + timedelta(days=20),
        "in_25_days": today + timedelta(days=25),
        "yesterday": today - timedelta(days=1),
    }
