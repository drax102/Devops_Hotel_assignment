import secrets
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import not_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

app = FastAPI(
    title="Hotel Reservation Service",
    description="Room Availability and Reservation API",
    version="1.0.0",
)


def generate_unique_booking_reference(db: Session, prefix: str = "BK") -> str:
    """Generate a collision-safe unique booking reference."""
    for _ in range(10):
        random_suffix = secrets.token_hex(4).upper()
        candidate = f"{prefix}-{random_suffix}"
        exists = (
            db.query(models.Reservation)
            .filter(models.Reservation.booking_reference == candidate)
            .first()
        )
        if not exists:
            return candidate
    raise RuntimeError(
        "Failed to generate unique booking reference after multiple attempts"
    )


@app.get("/")
def home():
    return {"message": "Hotel Reservation Service is running!", "docs_url": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "hotel-reservation-api"}


@app.post(
    "/rooms", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED
)
def create_room(room_in: schemas.RoomCreate, db: Session = Depends(get_db)):
    """Create a new hotel room."""
    existing = (
        db.query(models.Room)
        .filter(models.Room.room_number == room_in.room_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Room number {room_in.room_number} already exists",
        )

    room = models.Room(
        room_number=room_in.room_number,
        room_type=room_in.room_type,
        price_per_night=room_in.price_per_night,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@app.get("/rooms", response_model=list[schemas.RoomResponse])
def list_rooms(db: Session = Depends(get_db)):
    """List all hotel rooms."""
    return db.query(models.Room).all()


@app.get("/availability", response_model=list[schemas.RoomResponse])
def check_availability(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    room_type: str | None = Query(None, description="Optional room type filter"),
    db: Session = Depends(get_db),
):
    """
    Query available rooms for a given date range.
    Uses half-open intervals [check_in, check_out) so checkout date can equal next check-in.
    """
    if check_in < date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Check-in date cannot be in the past",
        )
    if check_out <= check_in:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Check-out date must be strictly after check-in date",
        )

    # Subquery: room IDs with confirmed overlapping reservations
    # Overlap occurs when: existing.check_in < query.check_out AND existing.check_out > query.check_in
    overlapping_subquery = (
        db.query(models.Reservation.room_id)
        .filter(
            models.Reservation.status == "confirmed",
            models.Reservation.check_in < check_out,
            models.Reservation.check_out > check_in,
        )
        .subquery()
    )

    query = db.query(models.Room).filter(
        not_(models.Room.id.in_(overlapping_subquery.select()))
    )

    if room_type:
        query = query.filter(models.Room.room_type.ilike(room_type))

    return query.all()


@app.post(
    "/reservations",
    response_model=schemas.ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    payload: schemas.ReservationCreate, db: Session = Depends(get_db)
):
    """
    Create a reservation for a room.
    Guarded by application checks AND the Postgres exclusion constraint against double-booking.
    """
    # 1. Verify target room exists
    room = db.query(models.Room).filter(models.Room.id == payload.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with id {payload.room_id} not found",
        )

    # 2. Application-level check (convenience layer)
    overlapping = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.room_id == payload.room_id,
            models.Reservation.status == "confirmed",
            models.Reservation.check_in < payload.check_out,
            models.Reservation.check_out > payload.check_in,
        )
        .first()
    )
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is already booked for the requested dates",
        )

    # 3. Create reservation and rely on DB exclusion constraint for atomic concurrency protection
    booking_ref = generate_unique_booking_reference(db)
    reservation = models.Reservation(
        booking_reference=booking_ref,
        customer_name=payload.customer_name,
        room_id=payload.room_id,
        check_in=payload.check_in,
        check_out=payload.check_out,
        status="confirmed",
    )

    try:
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room is already booked for the requested dates (concurrency conflict)",
        ) from None


@app.get(
    "/reservations/{booking_reference}", response_model=schemas.ReservationResponse
)
def get_reservation(booking_reference: str, db: Session = Depends(get_db)):
    """Retrieve reservation details by booking reference."""
    reservation = (
        db.query(models.Reservation)
        .filter(models.Reservation.booking_reference == booking_reference)
        .first()
    )
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with reference '{booking_reference}' not found",
        )
    return reservation
