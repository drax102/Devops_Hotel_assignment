from datetime import date, timedelta

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from app import models
from app.database import DATABASE_URL, get_db
from app.main import app

# 1. Dedicated test database URL
TEST_DB_NAME = "hotel_test_db"
TEST_DATABASE_URL = DATABASE_URL.set(database=TEST_DB_NAME)

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Ensure hotel_test_db exists and is fully migrated using Alembic.
    Never uses create_all/drop_all.
    """
    # Run Alembic migrations against hotel_test_db
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        TEST_DATABASE_URL.render_as_string(hide_password=False),
    )
    command.upgrade(alembic_cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean_test_tables():
    """Clean test tables between tests to ensure test isolation."""
    yield
    with test_engine.connect() as conn:
        conn.execute(
            text("TRUNCATE TABLE reservations, rooms RESTART IDENTITY CASCADE;")
        )
        conn.commit()


@pytest.fixture
def db_session():
    """Provide a database session connected strictly to hotel_test_db."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI TestClient configured to use hotel_test_db."""

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
    """Fixture providing a fresh test room in hotel_test_db."""
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
