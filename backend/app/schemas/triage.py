from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, conint, confloat

UrgencyLevel = Literal["EMERGENCY", "URGENT", "ROUTINE", "SELF_CARE"]
Gender = Literal["male", "female", "other"]
SupportedLanguage = Literal["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
QuestionType = Literal["yes_no", "choice", "scale", "free_text"]


class Location(BaseModel):
    """Example: {"lat":12.9716,"lng":77.5946}"""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class SymptomInput(BaseModel):
    """Example: {"symptoms":["fever","cough"],"patient_age":30,"patient_gender":"female","language":"en"}"""

    symptoms: str | list[str]
    patient_age: conint(ge=0, le=120)
    patient_gender: Gender
    location: Location | None = None
    language: SupportedLanguage
    follow_up_answers: dict[str, str] | None = None
    patient_id: str | None = None
    severity: conint(ge=1, le=10) | None = None
    duration_days: conint(ge=0, le=365) | None = None
    current_medications: list[str] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "symptoms": ["fever", "cough"],
                    "patient_age": 30,
                    "patient_gender": "female",
                    "location": {"lat": 12.9716, "lng": 77.5946},
                    "language": "en",
                    "follow_up_answers": {"breathing_trouble": "No"},
                    "severity": 5,
                    "duration_days": 2,
                    "current_medications": ["Paracetamol", "Aspirin"],
                }
            ]
        }
    )


class FollowUpQuestion(BaseModel):
    """Example: {"id":"breathing","question":"Are you short of breath?","type":"yes_no"}"""

    id: str
    question: str
    type: QuestionType
    options: list[str] | None = None
    reason: str | None = None


class FollowUpRequest(BaseModel):
    """Example: {"symptoms":"stomach pain","patient_age":7,"patient_gender":"male","language":"en"}"""

    symptoms: str | list[str]
    patient_age: conint(ge=0, le=120)
    patient_gender: Gender
    language: SupportedLanguage
    previous_answers: dict[str, str] | None = None


class FollowUpResponse(BaseModel):
    """Example: {"questions":[{"id":"vomiting","question":"Has vomiting started?","type":"yes_no"}]}"""

    questions: list[FollowUpQuestion]
    source: str = "hybrid"


class TriageResponse(BaseModel):
    """Example: {"urgency_level":"URGENT","confidence_score":0.82}"""

    urgency_level: UrgencyLevel
    confidence_score: confloat(ge=0.0, le=1.0)
    reasoning: str
    red_flags: list[str]
    care_pathway: str
    follow_up_questions: list[FollowUpQuestion]
    estimated_distance_to_facility: float | None = None
    cost_estimate_inr: dict | None = None
    follow_up_reminder_token: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "urgency_level": "URGENT",
                    "confidence_score": 0.82,
                    "reasoning": "Fever with breathing difficulty requires urgent care.",
                    "red_flags": ["shortness of breath"],
                    "care_pathway": "Visit a doctor within 24 hours.",
                    "follow_up_questions": ["Do you have chest pain?"],
                    "estimated_distance_to_facility": 2.5,
                }
            ]
        }
    )


class TriageCreate(BaseModel):
    """Example: {"patient_id":"uuid","symptoms":{"raw":"fever"},"urgency_level":"URGENT"}"""

    patient_id: str
    symptoms: dict
    urgency_level: UrgencyLevel
    confidence_score: confloat(ge=0.0, le=1.0)
    reasoning: str
    red_flags: list[str]
    care_pathway: str
    follow_up_questions: list[str]
    image_analysis: dict | None = None
    location_lat: float | None = Field(default=None, ge=-90, le=90)
    location_lng: float | None = Field(default=None, ge=-180, le=180)
    offline_mode: bool = False
    ai_model_used: str
    processing_time_ms: conint(ge=0)


class TriageHistoryEntry(BaseModel):
    """Example: {"created_at":"2026-02-06T10:00:00+05:30","urgency_level":"ROUTINE"}"""

    created_at: str
    urgency_level: UrgencyLevel
    confidence_score: confloat(ge=0.0, le=1.0)
    reasoning: str


class TriageHistoryResponse(BaseModel):
    """Example: {"trend":"worsening","sessions":[...]}"""

    trend: str
    sessions: list[TriageHistoryEntry]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trend": "worsening",
                    "sessions": [
                        {
                            "created_at": "2026-02-06T10:00:00+05:30",
                            "urgency_level": "URGENT",
                            "confidence_score": 0.78,
                            "reasoning": "Symptoms worsening over 48 hours.",
                        }
                    ],
                }
            ]
        }
    )
