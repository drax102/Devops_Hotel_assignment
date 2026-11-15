from datetime import timedelta

from fastapi import status


def test_health_endpoint(client):
    """Test health check returns 200 and healthy status (liveness)."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "hotel-reservation-api"


def test_ready_endpoint(client):
    """Test ready check returns 200 when database is connected (readiness)."""
    response = client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_request_id_header_injected(client):
    """Test that X-Request-ID is injected in response headers."""
    response = client.get("/health")
    assert "x-request-id" in response.headers
    custom_id = "test-custom-tracing-id-12345"
    response_with_custom = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response_with_custom.headers["x-request-id"] == custom_id


def test_create_and_list_rooms(client):
    """Test room creation and listing."""
    import secrets

    r_num = f"R{secrets.token_hex(2).upper()}"
    room_payload = {
        "room_number": r_num,
        "room_type": "Deluxe Suite",
        "price_per_night": 200,
    }
    create_res = client.post("/rooms", json=room_payload)
    assert create_res.status_code == status.HTTP_201_CREATED
    data = create_res.json()
    assert data["room_number"] == r_num
    assert data["room_type"] == "Deluxe Suite"
    assert data["price_per_night"] == 200
    assert "id" in data

    # Listing rooms should include created room
    list_res = client.get("/rooms")
    assert list_res.status_code == status.HTTP_200_OK
    rooms = list_res.json()
    assert any(r["room_number"] == r_num for r in rooms)


def test_create_duplicate_room_fails(client, test_room):
    """Test creating duplicate room number returns 409 conflict."""
    room_payload = {
        "room_number": test_room.room_number,
        "room_type": "Other",
        "price_per_night": 150,
    }
    res = client.post("/rooms", json=room_payload)
    assert res.status_code == status.HTTP_409_CONFLICT


def test_create_valid_reservation(client, test_room, relative_dates):
    """Test creating a reservation with valid future dates."""
    payload = {
        "customer_name": "Bob Smith",
        "room_id": test_room.id,
        "check_in": relative_dates["tomorrow"].isoformat(),
        "check_out": relative_dates["in_5_days"].isoformat(),
    }
    res = client.post("/reservations", json=payload)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["customer_name"] == "Bob Smith"
    assert data["room_id"] == test_room.id
    assert data["booking_reference"].startswith("BK-")
    assert data["status"] == "confirmed"

    # Verify retrieval by booking reference
    ref = data["booking_reference"]
    get_res = client.get(f"/reservations/{ref}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["booking_reference"] == ref


def test_reservation_past_dates_rejected(client, test_room, relative_dates):
    """Test that check-in date in the past is rejected with 422."""
    payload = {
        "customer_name": "Past Date Guest",
        "room_id": test_room.id,
        "check_in": relative_dates["yesterday"].isoformat(),
        "check_out": relative_dates["tomorrow"].isoformat(),
    }
    res = client.post("/reservations", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reservation_checkout_before_checkin_rejected(
    client, test_room, relative_dates
):
    """Test that check-out <= check-in is rejected with 422."""
    payload = {
        "customer_name": "Invalid Range Guest",
        "room_id": test_room.id,
        "check_in": relative_dates["in_5_days"].isoformat(),
        "check_out": relative_dates["in_5_days"].isoformat(),
    }
    res = client.post("/reservations", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reservation_nonexistent_room_returns_404(client, relative_dates):
    """Test booking a nonexistent room ID returns 404."""
    payload = {
        "customer_name": "Ghost Guest",
        "room_id": 999999,
        "check_in": relative_dates["tomorrow"].isoformat(),
        "check_out": relative_dates["in_5_days"].isoformat(),
    }
    res = client.post("/reservations", json=payload)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_adjacent_bookings_allowed(client, test_room, relative_dates):
    """
    Test adjacent bookings where Booking B check_in == Booking A check_out.
    Must be allowed (half-open interval [check_in, check_out)).
    """
    date_a_start = relative_dates["today"] + timedelta(days=20)
    date_a_end = relative_dates["today"] + timedelta(days=25)
    date_b_start = date_a_end  # Exact checkout day of booking A
    date_b_end = relative_dates["today"] + timedelta(days=30)

    # Booking A
    res_a = client.post(
        "/reservations",
        json={
            "customer_name": "Guest Alpha",
            "room_id": test_room.id,
            "check_in": date_a_start.isoformat(),
            "check_out": date_a_end.isoformat(),
        },
    )
    assert res_a.status_code == status.HTTP_201_CREATED

    # Booking B (adjacent)
    res_b = client.post(
        "/reservations",
        json={
            "customer_name": "Guest Beta",
            "room_id": test_room.id,
            "check_in": date_b_start.isoformat(),
            "check_out": date_b_end.isoformat(),
        },
    )
    assert res_b.status_code == status.HTTP_201_CREATED


def test_overlapping_booking_rejected(client, test_room, relative_dates):
    """Test overlapping booking returns 409 conflict."""
    start = relative_dates["today"] + timedelta(days=35)
    end = relative_dates["today"] + timedelta(days=40)

    # First booking
    res1 = client.post(
        "/reservations",
        json={
            "customer_name": "First Booker",
            "room_id": test_room.id,
            "check_in": start.isoformat(),
            "check_out": end.isoformat(),
        },
    )
    assert res1.status_code == status.HTTP_201_CREATED

    # Conflicting booking (partial overlap: days 37 to 42)
    res2 = client.post(
        "/reservations",
        json={
            "customer_name": "Second Booker",
            "room_id": test_room.id,
            "check_in": (start + timedelta(days=2)).isoformat(),
            "check_out": (end + timedelta(days=2)).isoformat(),
        },
    )
    assert res2.status_code == status.HTTP_409_CONFLICT


def test_availability_endpoint(client, test_room, relative_dates):
    """Test GET /availability properly reflects bookings."""
    start = relative_dates["today"] + timedelta(days=50)
    end = relative_dates["today"] + timedelta(days=55)

    # Check availability before booking
    res_before = client.get(
        f"/availability?check_in={start.isoformat()}&check_out={end.isoformat()}"
    )
    assert res_before.status_code == status.HTTP_200_OK
    available_rooms_before = [r["id"] for r in res_before.json()]
    assert test_room.id in available_rooms_before

    # Make booking
    book_res = client.post(
        "/reservations",
        json={
            "customer_name": "Availability Tester",
            "room_id": test_room.id,
            "check_in": start.isoformat(),
            "check_out": end.isoformat(),
        },
    )
    assert book_res.status_code == status.HTTP_201_CREATED

    # Check availability after booking (room should no longer be listed)
    res_after = client.get(
        f"/availability?check_in={start.isoformat()}&check_out={end.isoformat()}"
    )
    assert res_after.status_code == status.HTTP_200_OK
    available_rooms_after = [r["id"] for r in res_after.json()]
    assert test_room.id not in available_rooms_after
