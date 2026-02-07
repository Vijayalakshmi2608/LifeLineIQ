from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class RedFlagRule:
    condition: Callable[[str, dict], bool]
    reasoning: str
    action: str


RED_FLAG_RULES: dict[str, list[RedFlagRule]] = {
    "IMMEDIATE_EMERGENCY": [
        RedFlagRule(
            condition=lambda s, p: "chest pain" in s.lower() and p.get("age", 0) > 45,
            reasoning="Chest pain in adults over 45 may indicate heart attack.",
            action="Go to emergency immediately - call ambulance.",
        ),
        RedFlagRule(
            condition=lambda s, p: "difficulty breathing" in s.lower()
            and "blue lips" in s.lower(),
            reasoning="Blue lips with breathing difficulty indicates oxygen deprivation.",
            action="Call ambulance immediately.",
        ),
        RedFlagRule(
            condition=lambda s, p: "unconscious" in s.lower() or "unresponsive" in s.lower(),
            reasoning="Loss of consciousness requires immediate medical attention.",
            action="Call ambulance - do not delay.",
        ),
        RedFlagRule(
            condition=lambda s, p: "severe bleeding" in s.lower()
            or "heavy bleeding" in s.lower(),
            reasoning="Severe bleeding can lead to shock.",
            action="Apply pressure, call ambulance.",
        ),
        RedFlagRule(
            condition=lambda s, p: float(p.get("temperature", 0)) > 103 and p.get("age", 99) < 2,
            reasoning="High fever in infants can be dangerous.",
            action="Visit emergency within 1 hour.",
        ),
    ],
    "URGENT_CARE": [
        RedFlagRule(
            condition=lambda s, p: "fever" in s.lower()
            and "headache" in s.lower()
            and "stiff neck" in s.lower(),
            reasoning="Combination suggests possible meningitis.",
            action="Visit clinic within 4 hours.",
        ),
        RedFlagRule(
            condition=lambda s, p: "vomiting" in s.lower()
            and float(p.get("duration_days", 0)) > 2,
            reasoning="Persistent vomiting can lead to dehydration.",
            action="See doctor same day.",
        ),
    ],
}
