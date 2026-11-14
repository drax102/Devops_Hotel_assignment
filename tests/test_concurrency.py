import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from fastapi import status
from fastapi.testclient import TestClient

from app import models
from app.database import get_db
from app.main import app
from tests.conftest import TestingSessionLocal


def test_concurrent_conflicting_reservations():
    """
    CONCURRENCY ACCEPTANCE TEST:
    Simulates 10 concurrent requests attempting to book the exact same room
    for the exact same date range.

    Guarded by:
    1. Postgres exclusion constraint 'prevent_overlapping_reservations' (EXCLUDE USING gist).
    2. API translation of IntegrityError to HTTP 409 Conflict.

    Expected: Exactly 1 request succeeds with 201, 9 requests receive 409.
    """

    # Override get_db to yield independent test DB sessions per thread
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    db = TestingSessionLocal()
    # 1. Create a dedicated room for the concurrency test
    r_num = f"C{secrets.token_hex(3).upper()}"
    room = models.Room(
        room_number=r_num,
        room_type="Concurrency Test Suite",
        price_per_night=300,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    target_room_id = room.id
    db.close()

    # Dates far enough in the future
    start_date = date.today() + timedelta(days=90)
    end_date = date.today() + timedelta(days=95)

    def attempt_booking(thread_idx: int):
        with TestClient(app) as local_client:
            payload = {
                "customer_name": f"Concurrent User {thread_idx}",
                "room_id": target_room_id,
                "check_in": start_date.isoformat(),
                "check_out": end_date.isoformat(),
            }
            return local_client.post("/reservations", json=payload).status_code

    # 2. Fire 10 concurrent requests using ThreadPoolExecutor
    num_requests = 10
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        results = list(executor.map(attempt_booking, range(num_requests)))

    # 3. Assertions
    status_201_count = results.count(status.HTTP_201_CREATED)
    status_409_count = results.count(status.HTTP_409_CONFLICT)

    print(
        f"\n[CONCURRENCY RESULTS] Total: {len(results)}, 201 Created: {status_201_count}, 409 Conflict: {status_409_count}"
    )
    print(f"[CONCURRENCY RAW STATUS CODES] {results}")

    assert (
        len(results) == num_requests
    ), f"Expected {num_requests} responses, got {len(results)}"
    assert (
        status_201_count == 1
    ), f"Expected exactly ONE 201 Created, but got {status_201_count}"
    assert (
        status_409_count == num_requests - 1
    ), f"Expected {num_requests - 1} 409 Conflicts, but got {status_409_count}"

    # 4. Verify in DB directly: exactly 1 reservation exists for this room
    verify_db = TestingSessionLocal()
    try:
        confirmed_count = (
            verify_db.query(models.Reservation)
            .filter(
                models.Reservation.room_id == target_room_id,
                models.Reservation.status == "confirmed",
            )
            .count()
        )
        assert (
            confirmed_count == 1
        ), f"Database has {confirmed_count} confirmed reservations instead of 1"
    finally:
        verify_db.close()
        app.dependency_overrides.clear()
