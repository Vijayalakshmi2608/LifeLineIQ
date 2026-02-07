from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionFactory

STATE_CENTERS = {
    "UP": (26.85, 80.95),
    "Bihar": (25.60, 85.10),
    "MP": (23.25, 77.40),
    "Rajasthan": (26.90, 75.80),
    "Maharashtra": (19.10, 72.85),
}

FACILITY_TYPES = [("PHC", 0.60), ("CHC", 0.25), ("DH", 0.10), ("MEDICAL_COLLEGE", 0.03), ("PRIVATE", 0.02)]
SPECIALTIES = ["General", "Emergency", "Maternal Care", "Pediatrics", "Orthopedics"]


def pick_type() -> str:
    r = random.random()
    acc = 0
    for t, p in FACILITY_TYPES:
        acc += p
        if r <= acc:
            return t
    return "PHC"


def random_offset():
    return random.uniform(-0.5, 0.5)


def build_hours() -> dict:
    if random.random() < 0.1:
        return {"24/7": True}
    return {
        "monday": "09:00-17:00",
        "tuesday": "09:00-17:00",
        "wednesday": "09:00-17:00",
        "thursday": "09:00-17:00",
        "friday": "09:00-17:00",
        "saturday": "09:00-14:00",
    }


async def seed(count: int = 1000):
    async with AsyncSessionFactory() as session:  # type: AsyncSession
        rows = []
        for i in range(count):
            state, (lat, lng) = random.choice(list(STATE_CENTERS.items()))
            facility_type = pick_type()
            rows.append(
                {
                    "id": str(uuid.uuid4()),
                    "name": f"{state} Facility {i+1}",
                    "facility_type": facility_type,
                    "latitude": lat + random_offset(),
                    "longitude": lng + random_offset(),
                    "address": f"Sector {random.randint(1, 99)}",
                    "district": f"District {random.randint(1, 50)}",
                    "state": state,
                    "pincode": str(random.randint(100000, 999999)),
                    "contact_number": f"+91 9{random.randint(100000000, 999999999)}",
                    "emergency_available": facility_type in {"DH", "MEDICAL_COLLEGE", "PRIVATE"},
                    "operating_hours": build_hours(),
                    "specialties": random.sample(SPECIALTIES, k=2),
                    "bed_capacity": random.randint(10, 200),
                    "estimated_wait_time": random.randint(5, 90),
                    "is_active": True,
                    "last_updated": datetime.now(timezone.utc),
                }
            )

        await session.execute(
            text(
                """
                INSERT INTO facilities (
                    id, name, facility_type, latitude, longitude, address, district, state,
                    pincode, contact_number, emergency_available, operating_hours, specialties,
                    bed_capacity, estimated_wait_time, is_active, last_updated
                )
                VALUES (
                    :id, :name, :facility_type, :latitude, :longitude, :address, :district, :state,
                    :pincode, :contact_number, :emergency_available, :operating_hours, :specialties,
                    :bed_capacity, :estimated_wait_time, :is_active, :last_updated
                )
                """
            ),
            rows,
        )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
