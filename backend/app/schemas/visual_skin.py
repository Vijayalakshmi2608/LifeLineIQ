from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


UrgencyLevel = Literal["EMERGENCY", "URGENT", "ROUTINE", "SELF_CARE"]
QualityLevel = Literal["good", "fair", "poor"]


class VisualContext(BaseModel):
    body_locations: list[str] = Field(default_factory=list)
    duration: str | None = None
    associated_symptoms: list[str] = Field(default_factory=list)
    patient_description: str | None = None
    previous_treatment: str | None = None
    allergies: str | None = None
    language: str = "en"
    patient_age: int | None = None
    patient_gender: str | None = None
    patient_id: str | None = None


class ImageQuality(BaseModel):
    filename: str
    width: int
    height: int
    size_kb: int
    blur_score: float
    brightness: float
    quality: QualityLevel
    issues: list[str] = Field(default_factory=list)


class ConditionCandidate(BaseModel):
    name: str
    reason: str
    likelihood: str


class VisualAnalysisResponse(BaseModel):
    urgency_level: UrgencyLevel
    confidence: float = Field(ge=0, le=1)
    observations: list[str]
    possible_conditions: list[ConditionCandidate]
    red_flags: list[str]
    immediate_actions: list[str]
    home_care: list[str]
    when_to_seek_care: list[str]
    medications: list[str]
    specialist: str | None = None
    limitations: str
    quality: list[ImageQuality]
    stored_images: list[str] = Field(default_factory=list)
    saved_session_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
