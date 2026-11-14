import os
import sys

# Ensure app is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("Database connected successfully!")
        print(result.scalar())
except Exception as error:  # noqa: BLE001
    print("Database connection failed!")
    print(error)
