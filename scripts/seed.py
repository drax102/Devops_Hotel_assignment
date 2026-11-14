"""
Idempotent Database Seed Script
Seeds baseline rooms and bookings (including room 101 and BK001).
Uses dates relative to today to ensure testability and prevent past-date validation failures.
"""

import os
import sys
from datetime import date, timedelta

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import models
from app.database import SessionLocal


def seed_database():
    db = SessionLocal()
    try:
        print("[SEED] Starting idempotent database seed...")

        # 1. Baseline Rooms
        initial_rooms = [
            {"room_number": "101", "room_type": "Deluxe", "price_per_night": 150},
            {"room_number": "102", "room_type": "Standard", "price_per_night": 100},
            {"room_number": "201", "room_type": "Suite", "price_per_night": 250},
            {"room_number": "202", "room_type": "Standard", "price_per_night": 100},
        ]

        rooms_by_number = {}
        for room_data in initial_rooms:
            existing = (
                db.query(models.Room)
                .filter(models.Room.room_number == room_data["room_number"])
                .first()
            )

            if existing:
                print(
                    f"[SEED] Room {room_data['room_number']} already exists (ID: {existing.id}). Skipping."
                )
                rooms_by_number[room_data["room_number"]] = existing
            else:
                new_room = models.Room(**room_data)
                db.add(new_room)
                db.commit()
                db.refresh(new_room)
                print(
                    f"[SEED] Created room {new_room.room_number} (ID: {new_room.id})."
                )
                rooms_by_number[room_data["room_number"]] = new_room

        # 2. Baseline Reservation (BK001 on Room 101)
        today = date.today()
        bk001_existing = (
            db.query(models.Reservation)
            .filter(models.Reservation.booking_reference == "BK001")
            .first()
        )

        if bk001_existing:
            print(
                f"[SEED] Reservation BK001 already exists (ID: {bk001_existing.id}). Skipping."
            )
        else:
            room_101 = rooms_by_number.get("101")
            if room_101:
                # Booking 10 days out for 5 nights (strictly future relative to today)
                check_in = today + timedelta(days=10)
                check_out = today + timedelta(days=15)
                reservation = models.Reservation(
                    booking_reference="BK001",
                    customer_name="Alice Johnson",
                    room_id=room_101.id,
                    check_in=check_in,
                    check_out=check_out,
                    status="confirmed",
                )
                db.add(reservation)
                db.commit()
                db.refresh(reservation)
                print(
                    f"[SEED] Created baseline reservation BK001 for Room 101 ({check_in} to {check_out})."
                )

        print("[SEED] Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"[SEED ERROR] Error during seeding: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
