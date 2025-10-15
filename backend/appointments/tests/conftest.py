import sys
import os
import pytest
from datetime import datetime, date

@pytest.fixture
def fake_doctors():
    return [
        type("Doctor", (), {
            "id": 1,
            "full_name": "Dr. Alice",
            "specialization": "Therapist",
            "description": "Experienced doctor",
            "schedules": [
                type("Schedule", (), {
                    "date_": date(2025, 10, 13),
                    "available_slots": ["10:00", "11:00"]
                })()
            ],
            "appointments": [
                type("Appointment", (), {
                    "time": datetime(2025, 10, 13, 10, 0),
                    "status": "confirmed"
                })()
            ]
        })()
    ]
