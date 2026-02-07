from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from groq import Groq

from app.core.config import get_settings
from app.services.triage_engine import evaluate_triage

logger = logging.getLogger(__name__)

TRIAGE_PROMPT = """You are a medical triage assistant for rural India.

Patient Profile:
- Age: {age} years
- Gender: {gender}

Symptoms Reported:
{symptoms}

Task: Assess urgency level and provide clear guidance.

Output JSON format:
{{
    "urgency_level": "EMERGENCY" | "URGENT" | "ROUTINE" | "SELF_CARE",
    "confidence": 0.0-1.0,
    "reasoning": "Clear explanation in simple language (max 100 words)",
    "red_flags": ["symptom1", "symptom2"],
    "care_pathway": "Which specialist/facility type to visit",
    "follow_up_questions": [
        {{"question": "...", "type": "yes_no", "medical_reason": "..."}}
    ]
}}

CRITICAL RULES:
- Be conservative: if uncertain, escalate urgency
- Use 6th-grade reading level for explanations
- Include "what to watch for" in reasoning
- Red flags = symptoms requiring immediate attention
- Care pathway = specific facility type (PHC/CHC/Hospital/Specialist)
"""


class GroqAPIError(RuntimeError):
    pass


@dataclass
class GroqTriageConfig:
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.3
    max_tokens: int = 800
    timeout_seconds: int = 10
    retries: int = 3


class GroqTriageService:
    def __init__(self, api_key: str | None = None, config: GroqTriageConfig | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        try:
            self.client = Groq(api_key=self.api_key)
        except TypeError as exc:
            logger.error("Groq client init failed: %s", exc)
            self.client = None
        self.config = config or GroqTriageConfig()
        self._cache: dict[str, dict[str, Any]] = {}

    async def analyze_symptoms(self, symptoms: str, patient_profile: dict) -> dict:
        cache_key = f"{symptoms}|{patient_profile.get('age')}|{patient_profile.get('gender')}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        prompt = TRIAGE_PROMPT.format(
            age=patient_profile.get("age", "unknown"),
            gender=patient_profile.get("gender", "unknown"),
            symptoms=symptoms,
        )

        try:
            response = await self._call_groq(
                messages=[{"role": "user", "content": prompt}],
                json_mode=True,
            )
            validated = self._validate_triage_output(response)
            validated = self._apply_safety_layer(symptoms, validated)
            self._cache[cache_key] = validated
            return validated
        except GroqAPIError:
            fallback = await self.fallback_rule_based(symptoms)
            self._cache[cache_key] = fallback
            return fallback

    async def generate_follow_up_questions(
        self, initial_symptoms: str, patient_age: int
    ) -> list[dict]:
        age_band = "child" if patient_age < 12 else "elderly" if patient_age >= 65 else "adult"
        prompt = (
            "Generate 2-3 short follow-up questions for symptoms: "
            f"{initial_symptoms}. Patient is {age_band}. "
            "Return JSON array of objects with question, type, reason."
        )
        try:
            response = await self._call_groq(
                messages=[{"role": "user", "content": prompt}],
                json_mode=True,
            )
            if isinstance(response, list):
                return response
            return response.get("follow_up_questions", [])
        except GroqAPIError:
            return []

    async def explain_urgency(self, symptoms: dict, urgency_level: str) -> str:
        prompt = (
            "Explain in <=100 words, 6th-grade level, why urgency is "
            f"{urgency_level} for symptoms: {symptoms}. Include what to watch for."
        )
        response = await self._call_groq(
            messages=[{"role": "user", "content": prompt}],
            json_mode=False,
        )
        return str(response).strip()

    async def translate_to_language(self, text: str, target_language: str) -> str:
        prompt = (
            "Translate the following medical text accurately to "
            f"{target_language}. Keep technical terms in English if needed:\n{text}"
        )
        response = await self._call_groq(
            messages=[{"role": "user", "content": prompt}],
            json_mode=False,
        )
        return str(response).strip()

    async def _call_groq(self, messages: list[dict], json_mode: bool) -> Any:
        attempt = 0
        while True:
            attempt += 1
            start = time.time()
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self._sync_request, messages, json_mode),
                    timeout=self.config.timeout_seconds,
                )
                elapsed = (time.time() - start) * 1000
                logger.info("Groq call succeeded in %.2f ms", elapsed)
                return result
            except Exception as exc:
                elapsed = (time.time() - start) * 1000
                logger.warning("Groq call failed in %.2f ms: %s", elapsed, exc)
                if attempt >= self.config.retries:
                    raise GroqAPIError("Groq API unavailable") from exc
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

    def _sync_request(self, messages: list[dict], json_mode: bool) -> Any:
        if self.client is None:
            raise GroqAPIError("Groq client not available")
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"} if json_mode else None,
        )
        content = response.choices[0].message.content or ""
        if json_mode:
            return json.loads(content)
        return content

    def _validate_triage_output(self, data: dict) -> dict:
        required = {"urgency_level", "confidence", "reasoning", "red_flags", "care_pathway"}
        if not required.issubset(data):
            raise GroqAPIError("Incomplete triage response.")
        data["confidence"] = float(data.get("confidence", 0))
        return data

    def _apply_safety_layer(self, symptoms: str, data: dict) -> dict:
        lowered = symptoms.lower()
        if any(flag in lowered for flag in ["chest pain", "breathing", "unconscious"]):
            data["urgency_level"] = "EMERGENCY"
        if data.get("confidence", 0) < 0.7:
            data["reasoning"] = (
                data.get("reasoning", "")
                + " If symptoms worsen or you feel unsafe, seek urgent care."
            ).strip()
        data["reasoning"] = self._content_filter(data.get("reasoning", ""))
        return data

    def _content_filter(self, text: str) -> str:
        banned = ["harm", "violence", "suicide"]
        for word in banned:
            text = text.replace(word, "")
        return text.strip()

    async def fallback_rule_based(self, symptoms: str) -> dict:
        urgency, recommendation = await evaluate_triage(symptoms)
        return {
            "urgency_level": urgency.upper(),
            "confidence": 0.6,
            "reasoning": recommendation,
            "red_flags": [],
            "care_pathway": "PHC/CHC",
            "follow_up_questions": [],
        }
