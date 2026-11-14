from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RoomCreate(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    room_type: str = Field(min_length=1, max_length=30)
    price_per_night: int = Field(gt=0)


class RoomResponse(BaseModel):
    id: int
    room_number: str
    room_type: str
    price_per_night: int

    model_config = ConfigDict(from_attributes=True)


class ReservationCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    room_id: int = Field(gt=0)
    check_in: date
    check_out: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_in < date.today():
            raise ValueError("Check-in date cannot be in the past")

        if self.check_out <= self.check_in:
            raise ValueError("Check-out must be after check-in")

        return self


class ReservationResponse(BaseModel):
    id: int
    booking_reference: str
    customer_name: str
    room_id: int
    check_in: date
    check_out: date
    status: str

    model_config = ConfigDict(from_attributes=True)
