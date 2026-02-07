from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["SEVERE", "MODERATE", "MINOR"]


class MedicationItem(BaseModel):
    id: str
    name: str
    generic_name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class MedicationSearchResponse(BaseModel):
    items: list[MedicationItem]


class InteractionCheckRequest(BaseModel):
    current: list[str] = Field(default_factory=list)
    recommended: str
    language: str = "en"


class InteractionItem(BaseModel):
    drug1: str
    drug2: str
    severity: Severity
    description: str
    recommendation: str


class InteractionCheckResponse(BaseModel):
    interactions: list[InteractionItem]
    unknown_medications: list[str] = Field(default_factory=list)


class PatientMedicationCreate(BaseModel):
    patient_id: str
    medication_name: str
    dosage: str | None = None
    frequency: str | None = None


class PatientMedicationResponse(BaseModel):
    id: str
    patient_id: str
    medication_name: str
    dosage: str | None = None
    frequency: str | None = None
    is_active: bool
