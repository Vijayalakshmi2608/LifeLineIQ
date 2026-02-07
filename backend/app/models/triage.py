import enum
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class UrgencyLevel(str, enum.Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"
    SELF_CARE = "SELF_CARE"


class TriageSession(Base):
    __tablename__ = "triage_sessions"
    __table_args__ = (
        Index("ix_triage_created_at", "created_at"),
        Index("ix_triage_patient_created", "patient_id", "created_at"),
        Index("ix_triage_location_created", "location_lat", "location_lng", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    symptoms: Mapped[dict] = mapped_column(JSON)
    urgency_level: Mapped[UrgencyLevel] = mapped_column(String(20))
    confidence_score: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(Text)
    red_flags: Mapped[list] = mapped_column(JSON, default=list)
    care_pathway: Mapped[str] = mapped_column(Text)
    follow_up_questions: Mapped[list] = mapped_column(JSON, default=list)
    image_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)
    offline_mode: Mapped[bool] = mapped_column(default=False)
    visited_hospital: Mapped[bool] = mapped_column(default=False)
    ai_model_used: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processing_time_ms: Mapped[int] = mapped_column(Integer)
