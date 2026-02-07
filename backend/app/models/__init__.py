from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Ensure models are imported so metadata is populated for create_all.
from app.models import facility, follow_up, medication, outbreak, patient, symptom_translation, triage  # noqa: E402,F401
