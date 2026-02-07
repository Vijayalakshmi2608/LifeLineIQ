from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.triage import TriageSession
from app.models.patient import Patient
from app.schemas.visual_skin import VisualAnalysisResponse
from app.services.visual_skin_service import VisualSkinService

router = APIRouter(prefix="/visual", tags=["visual"])


@router.post("/analyze", response_model=VisualAnalysisResponse)
async def analyze_skin(
    files: list[UploadFile] = File(...),
    language: str = Form("en"),
    body_locations: str = Form(""),
    duration: str = Form(""),
    associated_symptoms: str = Form(""),
    patient_description: str = Form(""),
    previous_treatment: str = Form(""),
    allergies: str = Form(""),
    patient_age: str | None = Form(None),
    patient_gender: str | None = Form(None),
    patient_id: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    service = VisualSkinService()
    payload_files = []
    for item in files[:3]:
        content = await item.read()
        payload_files.append((item.filename, content))

    age_value = None
    if patient_age and str(patient_age).isdigit():
        age_value = int(patient_age)

    context = {
        "language": language,
        "body_locations": [x.strip() for x in body_locations.split(",") if x.strip()],
        "duration": duration,
        "associated_symptoms": [x.strip() for x in associated_symptoms.split(",") if x.strip()],
        "patient_description": patient_description,
        "previous_treatment": previous_treatment,
        "allergies": allergies,
        "patient_age": age_value,
        "patient_gender": patient_gender,
        "patient_id": patient_id,
    }
    analysis = await service.analyze(payload_files, context)
    stored_paths = service.save_images(payload_files)
    analysis["stored_images"] = [os.path.basename(p) for p in stored_paths]

    saved_session_id = None
    if patient_id:
        patient = await session.get(Patient, patient_id)
        if patient:
            triage = TriageSession(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                symptoms={"type": "skin_image", "context": context},
                urgency_level=analysis["urgency_level"],
                confidence_score=analysis.get("confidence", 0.6),
                reasoning="; ".join(analysis.get("observations", [])),
                red_flags=analysis.get("red_flags", []),
                care_pathway="Skin image analysis",
                follow_up_questions=[],
                image_analysis=analysis,
                offline_mode=False,
                ai_model_used=service.settings.groq_vision_model,
                created_at=datetime.now(timezone.utc),
                processing_time_ms=0,
            )
            session.add(triage)
            await session.commit()
            saved_session_id = triage.id

    analysis["saved_session_id"] = saved_session_id
    return analysis
