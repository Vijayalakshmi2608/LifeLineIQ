import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class SymptomTranslation(Base):
    __tablename__ = "symptom_translations"
    __table_args__ = (
        UniqueConstraint("language_code", "local_term", name="uq_lang_term"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    language_code: Mapped[str] = mapped_column(String(10))
    local_term: Mapped[str] = mapped_column(String(200))
    standard_term: Mapped[str] = mapped_column(String(200))
