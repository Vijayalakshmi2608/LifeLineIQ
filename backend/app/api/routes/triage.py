from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.database import get_session
from app.schemas.triage import FollowUpRequest, FollowUpResponse, SymptomInput, TriageResponse
from app.services.followup_reminder_service import FollowUpReminderService
from app.schemas.visual import VisualAnalysisResponse
from app.services.followup_service import FollowUpService
from app.services.groq_service import GroqTriageService
from app.services.symptom_mapper import SymptomMapper
from app.services.translation_service import TranslationService
from app.services.triage_engine import TriageEngine
from app.services.visual_analysis import VisualAnalysisService

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("/", response_model=TriageResponse)
async def run_triage(payload: SymptomInput, session=Depends(get_session)):
    try:
        groq = GroqTriageService()
        engine = TriageEngine(groq, session)
        followups = payload.follow_up_answers or {}
        if followups:
            followup_text = " | Follow-up answers: " + ", ".join(
                f"{key}={value}" for key, value in followups.items()
            )
        else:
            followup_text = ""
        mapper = SymptomMapper(session)
        translator = TranslationService()
        raw_symptoms = payload.symptoms
        if isinstance(raw_symptoms, list):
            raw_symptoms = ", ".join(raw_symptoms)
        mapped_terms = await mapper.map_terms(str(raw_symptoms), payload.language)
        mapped_text = ", ".join(mapped_terms)
        if payload.language != "en":
            mapped_text = translator.translate(mapped_text, payload.language, "en")

        patient_id = payload.patient_id or "anonymous"
        result = await engine.analyze(
            symptoms=f"{mapped_text}{followup_text}",
            patient_id=patient_id,
            patient_profile={
                "age": payload.patient_age,
                "gender": payload.patient_gender,
            },
            severity_score=float(payload.severity) if payload.severity else None,
            reported_duration_days=payload.duration_days,
            location=payload.location.model_dump() if payload.location else None,
        )
        triage = result["triage"]
        # Schedule follow-up if patient_id provided and triage saved
        reminder = None
        if patient_id != "anonymous" and result.get("triage_session_id"):
            service = FollowUpReminderService(session)
            reminder = await service.schedule_from_triage(
                patient_id=patient_id,
                triage_session_id=result["triage_session_id"],
                urgency_level=triage.get("urgency_level", "ROUTINE"),
                language=payload.language,
            )
        followups = triage.get("follow_up_questions", [])
        normalized_followups = []
        for idx, item in enumerate(followups):
            if isinstance(item, str):
                normalized_followups.append(
                    {"id": f"q{idx+1}", "question": item, "type": "yes_no"}
                )
            elif isinstance(item, dict):
                normalized_followups.append(
                    {
                        "id": item.get("id") or f"q{idx+1}",
                        "question": item.get("question") or item.get("text") or "",
                        "type": item.get("type") or "yes_no",
                        "options": item.get("options"),
                        "reason": item.get("medical_reason") or item.get("reason"),
                    }
                )
        urgency = triage.get("urgency_level", "ROUTINE")
        care_pathway = (triage.get("care_pathway") or "").lower()
        facility_map = {
            "phc": {"min_inr": 100, "max_inr": 500, "note": "PHC consultation"},
            "chc": {"min_inr": 300, "max_inr": 1500, "note": "CHC visit"},
            "hospital": {"min_inr": 800, "max_inr": 5000, "note": "Hospital OPD"},
            "specialist": {"min_inr": 1200, "max_inr": 7000, "note": "Specialist consult"},
            "private": {"min_inr": 1500, "max_inr": 12000, "note": "Private facility"},
        }
        urgency_map = {
            "EMERGENCY": {"min_inr": 5000, "max_inr": 20000, "note": "ER visit and urgent tests"},
            "URGENT": {"min_inr": 800, "max_inr": 5000, "note": "Same-day clinic visit"},
            "ROUTINE": {"min_inr": 300, "max_inr": 1500, "note": "Routine consultation"},
            "SELF_CARE": {"min_inr": 0, "max_inr": 300, "note": "Over-the-counter care"},
        }
        cost_estimate = None
        for key, value in facility_map.items():
            if key in care_pathway:
                cost_estimate = {**value, "facility_type": key.upper()}
                break
        if not cost_estimate:
            cost_estimate = urgency_map.get(urgency, urgency_map["ROUTINE"])
        reasoning = triage.get("reasoning", "")
        care_pathway = triage.get("care_pathway", "")
        if payload.language != "en":
            reasoning = translator.translate(reasoning, "en", payload.language)
            care_pathway = translator.translate(care_pathway, "en", payload.language)

        return {
            "urgency_level": triage["urgency_level"],
            "confidence_score": triage.get("confidence", 0.6),
            "reasoning": reasoning,
            "red_flags": triage.get("red_flags", []),
            "care_pathway": care_pathway,
            "follow_up_questions": normalized_followups,
            "estimated_distance_to_facility": None,
            "cost_estimate_inr": cost_estimate,
            "follow_up_reminder_token": reminder.token if reminder else None,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/followup", response_model=FollowUpResponse)
async def generate_followup(payload: FollowUpRequest):
    try:
        groq = GroqTriageService()
        service = FollowUpService(groq)
        questions = await service.generate(
            symptoms=payload.symptoms,
            patient_age=payload.patient_age,
            patient_gender=payload.patient_gender,
            previous_answers=payload.previous_answers,
        )
        return {"questions": questions, "source": "hybrid"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/visual", response_model=VisualAnalysisResponse)
async def analyze_visual(file: UploadFile = File(...)):
    try:
        content = await file.read()
        service = VisualAnalysisService()
        result = service.analyze(content)
        return {
            "urgency_level": result.urgency_level,
            "confidence_score": result.confidence_score,
            "findings": result.findings,
            "reference_images": [],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
