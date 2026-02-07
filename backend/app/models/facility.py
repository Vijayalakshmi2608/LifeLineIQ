import uuid

import enum

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class FacilityType(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"
    SDH = "SDH"
    DH = "DH"
    MEDICAL_COLLEGE = "MEDICAL_COLLEGE"
    PRIVATE = "PRIVATE"


class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (
        Index(
            "ix_facilities_geo",
            "latitude",
            "longitude",
            postgresql_using="gist",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    facility_type: Mapped[FacilityType] = mapped_column(String(30))
    latitude: Mapped[float] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float] = mapped_column(Numeric(11, 8))
    address: Mapped[str] = mapped_column(Text)
    district: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(120))
    pincode: Mapped[str] = mapped_column(String(6))
    contact_number: Mapped[str] = mapped_column(String(15))
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    operating_hours: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    specialties: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    bed_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_wait_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_updated: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
