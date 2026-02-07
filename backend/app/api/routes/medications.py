from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.medication import (
    InteractionCheckRequest,
    InteractionCheckResponse,
    MedicationSearchResponse,
    PatientMedicationCreate,
    PatientMedicationResponse,
)
from app.services.medication_service import MedicationService

router = APIRouter(prefix="/medications", tags=["medications"])


@router.get("/search", response_model=MedicationSearchResponse)
async def search_medications(
    q: str = Query("", min_length=1), session: AsyncSession = Depends(get_session)
):
    service = MedicationService(session)
    items = await service.search(q, limit=10)
    return {"items": items}


@router.post("/check-interactions", response_model=InteractionCheckResponse)
async def check_interactions(
    payload: InteractionCheckRequest, session: AsyncSession = Depends(get_session)
):
    service = MedicationService(session)
    interactions, unknown = await service.check_interactions(
        current=payload.current, recommended=payload.recommended
    )
    return {"interactions": interactions, "unknown_medications": unknown}


@router.post("/patients/medications", response_model=PatientMedicationResponse)
async def add_patient_medication(
    payload: PatientMedicationCreate, session: AsyncSession = Depends(get_session)
):
    service = MedicationService(session)
    record = await service.add_patient_medication(
        patient_id=payload.patient_id,
        medication_name=payload.medication_name,
        dosage=payload.dosage,
        frequency=payload.frequency,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Medication not found")
    return {
        "id": record.id,
        "patient_id": record.patient_id,
        "medication_name": payload.medication_name,
        "dosage": record.dosage,
        "frequency": record.frequency,
        "is_active": record.is_active,
    }


@router.get("/patients/{patient_id}/medications", response_model=list[PatientMedicationResponse])
async def list_patient_medications(
    patient_id: str, session: AsyncSession = Depends(get_session)
):
    service = MedicationService(session)
    return await service.list_patient_medications(patient_id)
