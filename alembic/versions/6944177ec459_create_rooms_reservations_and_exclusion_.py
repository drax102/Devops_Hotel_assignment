"""create_rooms_reservations_and_exclusion_constraint

Revision ID: 6944177ec459
Revises:
Create Date: 2026-11-14 23:57:06.770825

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6944177ec459"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable btree_gist extension for combining scalar and range types in GiST indexes
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 2. Create rooms table
    op.create_table(
        "rooms",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("room_number", sa.String(length=10), nullable=False, unique=True),
        sa.Column("room_type", sa.String(length=30), nullable=False),
        sa.Column("price_per_night", sa.Integer(), nullable=False),
    )
    op.create_index("ix_rooms_id", "rooms", ["id"], unique=False)

    # 3. Create reservations table
    op.create_table(
        "reservations",
        sa.Column(
            "id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column(
            "booking_reference", sa.String(length=20), nullable=False, unique=True
        ),
        sa.Column("customer_name", sa.String(length=100), nullable=False),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("rooms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="confirmed"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("check_out > check_in", name="valid_reservation_dates"),
    )
    op.create_index("ix_reservations_id", "reservations", ["id"], unique=False)
    op.create_index(
        "ix_reservations_booking_reference",
        "reservations",
        ["booking_reference"],
        unique=True,
    )
    op.create_index(
        "ix_reservations_room_id", "reservations", ["room_id"], unique=False
    )

    # 4. Create Postgres exclusion constraint preventing overlapping reservations for the same room
    # Uses half-open interval [check_in, check_out) so check_out == next check_in is permitted
    op.execute("""
        ALTER TABLE reservations
        ADD CONSTRAINT prevent_overlapping_reservations
        EXCLUDE USING gist (
            room_id WITH =,
            daterange(check_in, check_out, '[)') WITH &&
        )
        WHERE (status = 'confirmed');
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE reservations DROP CONSTRAINT IF EXISTS prevent_overlapping_reservations;"
    )
    op.drop_table("reservations")
    op.drop_table("rooms")
    op.execute("DROP EXTENSION IF EXISTS btree_gist;")
