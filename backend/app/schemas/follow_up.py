from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

UrgencyLevel = Literal["EMERGENCY", "URGENT", "ROUTINE", "SELF_CARE"]
ResponseStatus = Literal["better", "same", "worse", "skipped"]


class FollowUpSchedule(BaseModel):
    patient_id: str
    triage_session_id: str
    urgency_level: UrgencyLevel
    language: str = "en"


class FollowUpReminderResponse(BaseModel):
    token: str
    scheduled_time: datetime
    sent_at: datetime | None = None
    response_status: ResponseStatus | None = None
    urgency_level: UrgencyLevel
    deep_link: str

    model_config = ConfigDict(from_attributes=True)


class FollowUpPublic(BaseModel):
    token: str
    urgency_level: UrgencyLevel
    scheduled_time: datetime
    sent_at: datetime | None = None
    response_status: ResponseStatus | None = None
    triage_reasoning: str | None = None
    care_pathway: str | None = None


class FollowUpResponsePayload(BaseModel):
    response_status: ResponseStatus
    new_symptoms: str | None = None
    need_help: bool | None = None


class FollowUpMetrics(BaseModel):
    total_sent: int
    total_responded: int
    improved: int
    same: int
    worse: int
    response_rate: float
