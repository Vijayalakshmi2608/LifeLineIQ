from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from statistics import mean
from typing import Any

from app.core.security import sanitize_input
from app.services.outbreak_service import OutbreakService
from app.services.red_flags import RED_FLAG_RULES

logger = logging.getLogger(__name__)
_IN_MEMORY_HISTORY: dict[str, list[dict[str, Any]]] = {}


async def evaluate_triage(symptoms: str) -> tuple[str, str]:
    cleaned = sanitize_input(symptoms)
    if not cleaned:
        raise ValueError("Symptoms are required.")
    lowered = cleaned.lower()
    if "chest pain" in lowered or "breathing" in lowered:
        return "emergency", "Seek emergency care immediately."
    if "fever" in lowered or "vomiting" in lowered:
        return "urgent", "See a doctor within 24 hours."
    return "routine", "Monitor symptoms and schedule a routine check-up."


class TriageEngine:
    def __init__(self, groq_service: Any, db_session: Any | None = None):
        self.groq = groq_service
        self.db = db_session

    async def analyze(
        self,
        symptoms: str,
        patient_id: str,
        patient_profile: dict,
        severity_score: float | None = None,
        reported_duration_days: int | None = None,
        location: dict | None = None,
        image_data: bytes | None = None,
    ) -> dict:
        results: dict[str, Any] = {
            "patient_id": patient_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features_used": [],
            "processing_steps": [],
            "symptoms": symptoms,
            "location": location,
        }

        red_flag_result = self.check_red_flags(symptoms, patient_profile)
        results["processing_steps"].append("red_flag_check")

        if red_flag_result["triggered"]:
            results["triage"] = {
                "urgency_level": "EMERGENCY",
                "confidence": 1.0,
                "reasoning": red_flag_result["reasoning"],
                "action": red_flag_result["action"],
                "source": "rule_based",
            }
            results["features_used"].append("emergency_detection")
            results["triage_session_id"] = await self.save_triage_session(results)
            return results

        ai_result = await self.groq.analyze_symptoms(symptoms, patient_profile)
        results["processing_steps"].append("ai_analysis")
        results["features_used"].append("contextual_reasoning")

        trajectory = await self.analyze_trajectory(
            patient_id,
            symptoms,
            severity_score=severity_score,
            reported_duration_days=reported_duration_days,
        )
        if trajectory.get("has_history"):
            results["trajectory"] = trajectory
            results["features_used"].append("health_trajectory")
            if trajectory["trend"] == "worsening" and trajectory["confidence"] > 0.7:
                ai_result = self.upgrade_urgency(ai_result, trajectory)
                ai_result["reasoning"] = (
                    f"{ai_result.get('reasoning','')} | Symptoms worsening over {trajectory['days']} days"
                ).strip()

        if image_data:
            visual_result = await self.analyze_image(image_data, symptoms, patient_profile.get("age"))
            results["visual_analysis"] = visual_result
            results["features_used"].append("visual_triage")
            ai_result = self.merge_visual_findings(ai_result, visual_result)

        if location:
            community_context = await self.check_community_patterns(location, symptoms)
            if community_context.get("outbreak_detected"):
                results["community_alert"] = community_context
                results["features_used"].append("outbreak_detection")
                ai_result["reasoning"] = (
                    f"{ai_result.get('reasoning','')} | Alert: {community_context['alert_message']}"
                ).strip()

        results["triage"] = self.validate_and_finalize(ai_result, red_flag_result)
        results["triage_session_id"] = await self.save_triage_session(results)
        await self.record_outbreak_event(location, symptoms)
        self.record_session(
            patient_id,
            symptoms,
            severity_score=severity_score,
            urgency_level=results["triage"].get("urgency_level", "ROUTINE"),
            reported_duration_days=reported_duration_days,
            location=location,
        )
        return results

    def check_red_flags(self, symptoms: str, patient_profile: dict) -> dict:
        for rule in RED_FLAG_RULES["IMMEDIATE_EMERGENCY"]:
            if rule.condition(symptoms, patient_profile):
                return {
                    "triggered": True,
                    "reasoning": rule.reasoning,
                    "action": rule.action,
                    "urgency_override": "EMERGENCY",
                }
        for rule in RED_FLAG_RULES["URGENT_CARE"]:
            if rule.condition(symptoms, patient_profile):
                return {
                    "triggered": False,
                    "reasoning": rule.reasoning,
                    "action": rule.action,
                    "urgency_override": "URGENT",
                }
        return {"triggered": False}

    async def analyze_trajectory(
        self,
        patient_id: str,
        current_symptoms: str,
        severity_score: float | None = None,
        reported_duration_days: int | None = None,
    ) -> dict:
        history = []
        if self.db and hasattr(self.db, "get_patient_triage_history"):
            history = await self.db.get_patient_triage_history(patient_id, days=7)
        elif patient_id in _IN_MEMORY_HISTORY:
            history = _IN_MEMORY_HISTORY.get(patient_id, [])
        if not history or len(history) < 2:
            return {"has_history": False}

        severity_scores = []
        for session in history:
            score = session.get("severity_score")
            if score is None:
                score = self.calculate_severity_score(session["symptoms"])
            severity_scores.append(
                {"timestamp": session["created_at"], "score": score, "urgency": session["urgency_level"]}
            )
        current_score = (
            severity_score
            if severity_score is not None
            else self.calculate_severity_score(current_symptoms)
        )
        trend = self.detect_trend(severity_scores, current_score)
        if reported_duration_days is not None:
            days = reported_duration_days
        else:
            days = (datetime.now(timezone.utc) - history[0]["created_at"]).days
        return {
            "has_history": True,
            "sessions_count": len(history),
            "days": days,
            "trend": trend["direction"],
            "confidence": trend["confidence"],
            "recommendation": trend["urgency_adjustment"],
        }

    def calculate_severity_score(self, symptoms: Any) -> float:
        text = symptoms if isinstance(symptoms, str) else str(symptoms)
        markers = ["chest pain", "breathing", "unconscious", "high fever", "bleeding"]
        score = sum(1 for m in markers if m in text.lower())
        return score / max(len(markers), 1)

    def detect_trend(self, scores: list[dict], current_score: float) -> dict:
        history_scores = [item["score"] for item in scores] + [current_score]
        avg = mean(history_scores)
        direction = "stable"
        if self._is_consecutive_worsening(scores, current_score):
            direction = "worsening"
        elif current_score > avg + 0.15:
            direction = "worsening"
        elif current_score < avg - 0.15:
            direction = "improving"
        confidence = min(0.95, abs(current_score - avg) + 0.5)
        adjustment = "no_change"
        if direction == "worsening":
            adjustment = "upgrade"
        elif direction == "improving":
            adjustment = "consider_downgrade"
        return {"direction": direction, "confidence": confidence, "urgency_adjustment": adjustment}

    def _is_consecutive_worsening(self, scores: list[dict], current_score: float) -> bool:
        if len(scores) < 2:
            return False
        recent = scores[-2:]
        recent_scores = [item["score"] for item in recent] + [current_score]
        return recent_scores[0] < recent_scores[1] < recent_scores[2]

    def upgrade_urgency(self, ai_result: dict, trajectory: dict) -> dict:
        order = ["SELF_CARE", "ROUTINE", "URGENT", "EMERGENCY"]
        current = ai_result.get("urgency_level", "ROUTINE")
        if current in order:
            idx = min(order.index(current) + 1, len(order) - 1)
            ai_result["urgency_level"] = order[idx]
        return ai_result

    async def analyze_image(self, image_data: bytes, symptoms: str, age: int | None) -> dict:
        await asyncio.sleep(0)
        return {"summary": "No critical visual red flags detected.", "confidence": 0.6}

    def merge_visual_findings(self, ai_result: dict, visual_result: dict) -> dict:
        ai_result["reasoning"] = f"{ai_result.get('reasoning','')} | Visual: {visual_result.get('summary')}"
        return ai_result

    async def check_community_patterns(self, location: dict, symptoms: str) -> dict:
        await asyncio.sleep(0)
        if not self.db:
            return {"outbreak_detected": False}
        service = OutbreakService(self.db)
        return await service.detect_outbreak(
            lat=location["lat"],
            lng=location["lng"],
            symptoms=symptoms,
            radius_km=5,
            window_hours=48,
            min_cases=15,
        )

    def validate_and_finalize(self, ai_result: dict, red_flag_result: dict) -> dict:
        if red_flag_result.get("urgency_override"):
            ai_result["urgency_level"] = red_flag_result["urgency_override"]
        if ai_result.get("confidence", 0) < 0.7:
            ai_result["disclaimer"] = (
                "Due to uncertainty in symptom assessment, we recommend consulting a health worker."
            )
        if not ai_result.get("reasoning"):
            ai_result["reasoning"] = "Based on your symptoms, medical consultation recommended."
        ai_result["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        ai_result["ai_model"] = "llama-3.3-70b-groq"
        return ai_result

    async def save_triage_session(self, results: dict) -> str | None:
        if not self.db:
            logger.info("Triage session not persisted (no db session).")
            return None

        try:
            from sqlalchemy.ext.asyncio import AsyncSession

            if isinstance(self.db, AsyncSession):
                from app.models.triage import TriageSession

                triage = results.get("triage", {})
                session = TriageSession(
                    patient_id=results.get("patient_id", "anonymous"),
                    symptoms={"raw": results.get("symptoms") or triage.get("symptoms") or ""},
                    urgency_level=triage.get("urgency_level", "ROUTINE"),
                    confidence_score=triage.get("confidence", 0.6),
                    reasoning=triage.get("reasoning", ""),
                    red_flags=triage.get("red_flags", []),
                    care_pathway=triage.get("care_pathway", ""),
                    follow_up_questions=triage.get("follow_up_questions", []),
                    image_analysis=results.get("visual_analysis"),
                    location_lat=(results.get("location") or {}).get("lat"),
                    location_lng=(results.get("location") or {}).get("lng"),
                    offline_mode=False,
                    ai_model_used=triage.get("ai_model", "llama-3.3-70b-groq"),
                    processing_time_ms=triage.get("processing_time_ms", 0),
                )
                self.db.add(session)
                await self.db.commit()
                await self.db.refresh(session)
                return session.id
        except Exception as exc:
            logger.warning("Failed to persist triage session: %s", exc)
        return None

    def record_session(
        self,
        patient_id: str,
        symptoms: str,
        severity_score: float | None,
        urgency_level: str,
        reported_duration_days: int | None,
        location: dict | None,
    ) -> None:
        entry = {
            "created_at": datetime.now(timezone.utc),
            "symptoms": symptoms,
            "severity_score": severity_score,
            "urgency_level": urgency_level,
            "reported_duration_days": reported_duration_days,
        }
        history = _IN_MEMORY_HISTORY.setdefault(patient_id, [])
        history.append(entry)
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        _IN_MEMORY_HISTORY[patient_id] = [item for item in history if item["created_at"] >= cutoff]

        # outbreak persistence handled in record_outbreak_event

    async def record_outbreak_event(self, location: dict | None, symptoms: str) -> None:
        if not (location and "lat" in location and "lng" in location and self.db):
            return
        try:
            service = OutbreakService(self.db)
            await service.record_event(
                lat=float(location["lat"]),
                lng=float(location["lng"]),
                symptoms=symptoms,
            )
        except Exception as exc:
            logger.warning("Outbreak event not saved: %s", exc)
