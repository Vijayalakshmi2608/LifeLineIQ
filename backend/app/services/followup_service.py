from __future__ import annotations

import logging
from typing import Any

from app.services.groq_service import GroqAPIError, GroqTriageService

logger = logging.getLogger(__name__)


class FollowUpService:
    def __init__(self, groq: GroqTriageService | None = None):
        self.groq = groq or GroqTriageService()

    async def generate(
        self,
        symptoms: str | list[str],
        patient_age: int,
        patient_gender: str,
        previous_answers: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        normalized = self._normalize_symptoms(symptoms)
        previous_answers = previous_answers or {}

        questions: list[dict[str, Any]] = []
        questions.extend(self._rule_questions(normalized, patient_age, patient_gender))

        try:
            ai_questions = await self.groq.generate_follow_up_questions(
                initial_symptoms=normalized, patient_age=patient_age
            )
            questions.extend(self._normalize_ai_questions(ai_questions))
        except GroqAPIError as exc:
            logger.warning("Groq follow-up fallback: %s", exc)

        deduped = self._dedupe_questions(questions)
        filtered = [q for q in deduped if q["id"] not in previous_answers]

        return filtered[:3]

    def _normalize_symptoms(self, symptoms: str | list[str]) -> str:
        if isinstance(symptoms, list):
            return ", ".join([s for s in symptoms if s])
        return str(symptoms)

    def _rule_questions(
        self, symptoms: str, patient_age: int, patient_gender: str
    ) -> list[dict[str, Any]]:
        lowered = symptoms.lower()
        questions: list[dict[str, Any]] = []

        if patient_age < 12:
            questions.extend(
                [
                    {
                        "id": "child_appetite",
                        "question": "Has the child been eating or drinking less than usual?",
                        "type": "yes_no",
                        "reason": "Reduced intake can indicate dehydration.",
                    },
                    {
                        "id": "child_urine",
                        "question": "Has the child had fewer wet diapers or urinated less today?",
                        "type": "yes_no",
                        "reason": "Low urine output can be a warning sign.",
                    },
                ]
            )
        elif patient_age >= 65:
            questions.extend(
                [
                    {
                        "id": "elderly_chest_pain",
                        "question": "Are you experiencing any chest pain or pressure?",
                        "type": "yes_no",
                        "reason": "Cardiac screening is important in older adults.",
                    },
                    {
                        "id": "elderly_breathing",
                        "question": "Are you more short of breath than usual?",
                        "type": "yes_no",
                        "reason": "Breathing difficulty can indicate urgent issues.",
                    },
                ]
            )

        if any(word in lowered for word in ["stomach", "abdomen", "abdominal", "belly"]):
            questions.extend(
                [
                    {
                        "id": "vomiting",
                        "question": "Have you vomited in the last 24 hours?",
                        "type": "yes_no",
                        "reason": "Vomiting changes urgency and dehydration risk.",
                    },
                    {
                        "id": "diarrhea",
                        "question": "Have you had diarrhea today?",
                        "type": "yes_no",
                        "reason": "Diarrhea can cause fluid loss quickly.",
                    },
                    {
                        "id": "food_intake",
                        "question": "Did symptoms start after eating outside food?",
                        "type": "yes_no",
                        "reason": "Helps identify possible food-related illness.",
                    },
                ]
            )

        if "fever" in lowered:
            questions.append(
                {
                    "id": "high_fever",
                    "question": "Is the fever above 101°F (38.3°C)?",
                    "type": "yes_no",
                    "reason": "Higher fever suggests more urgent evaluation.",
                }
            )

        if any(word in lowered for word in ["cough", "breathing", "shortness"]):
            questions.append(
                {
                    "id": "breathing_trouble",
                    "question": "Are you having trouble breathing at rest?",
                    "type": "yes_no",
                    "reason": "Breathing difficulty may require urgent care.",
                }
            )

        if any(word in lowered for word in ["chest", "pain", "pressure"]):
            questions.append(
                {
                    "id": "chest_pain",
                    "question": "Does the chest pain spread to your arm, jaw, or back?",
                    "type": "yes_no",
                    "reason": "Radiating pain can signal a cardiac emergency.",
                }
            )

        if patient_gender == "female" and "pain" in lowered:
            questions.append(
                {
                    "id": "pregnancy",
                    "question": "Is there any chance you could be pregnant?",
                    "type": "yes_no",
                    "reason": "Pregnancy affects the triage pathway.",
                }
            )

        return questions

    def _normalize_ai_questions(self, questions: Any) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        if not isinstance(questions, list):
            return normalized
        for idx, item in enumerate(questions):
            if not isinstance(item, dict):
                continue
            text = str(item.get("question") or item.get("text") or "").strip()
            if not text:
                continue
            qid = item.get("id") or f"ai_q{idx + 1}"
            qtype = item.get("type") or "yes_no"
            normalized.append(
                {
                    "id": str(qid),
                    "question": text,
                    "type": qtype if qtype in {"yes_no", "choice", "scale", "free_text"} else "yes_no",
                    "options": item.get("options"),
                    "reason": item.get("reason") or item.get("medical_reason"),
                }
            )
        return normalized

    def _dedupe_questions(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for q in questions:
            key = f"{q.get('id')}|{q.get('question')}"
            if key in seen:
                continue
            seen.add(key)
            result.append(q)
        return result
