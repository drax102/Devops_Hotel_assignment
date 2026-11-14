
from fastapi import FastAPI

app = FastAPI(
    title="Hotel Reservation Service",
    description="Room Availability and Reservation API",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Hotel Reservation Service is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "hotel-reservation-api"
    }
