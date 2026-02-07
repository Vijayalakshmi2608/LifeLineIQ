import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class FollowUpReminder(Base):
    __tablename__ = "follow_up_reminders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    triage_session_id: Mapped[str] = mapped_column(ForeignKey("triage_sessions.id"))
    urgency_level: Mapped[str] = mapped_column(String(20))
    scheduled_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_received_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    channel: Mapped[str] = mapped_column(String(16), default="whatsapp")
    message_language: Mapped[str] = mapped_column(String(8), default="en")
    deep_link: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
