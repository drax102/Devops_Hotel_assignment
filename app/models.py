from datetime import UTC, date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    room_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    room_type: Mapped[str] = mapped_column(String(30), nullable=False)

    price_per_night: Mapped[int] = mapped_column(Integer, nullable=False)

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="room")


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    booking_reference: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )

    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)

    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)

    check_in: Mapped[date] = mapped_column(Date, nullable=False)

    check_out: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    room: Mapped["Room"] = relationship(back_populates="reservations")

    __table_args__ = (
        CheckConstraint("check_out > check_in", name="valid_reservation_dates"),
    )
