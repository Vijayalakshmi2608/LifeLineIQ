import uuid

from sqlalchemy import DateTime, Float, String, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class OutbreakEvent(Base):
    __tablename__ = "outbreak_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    symptoms_text: Mapped[str] = mapped_column(String(500))
    symptoms_tokens: Mapped[list] = mapped_column(JSON, default=list)
