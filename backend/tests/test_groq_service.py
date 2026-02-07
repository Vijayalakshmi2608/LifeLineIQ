import asyncio
import unittest

from app.services.groq_service import GroqTriageService


class GroqServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = GroqTriageService(api_key="test")

    def test_emergency_escalation(self):
        data = {
            "urgency_level": "ROUTINE",
            "confidence": 0.8,
            "reasoning": "Mild symptoms.",
            "red_flags": [],
            "care_pathway": "PHC",
        }
        out = self.service._apply_safety_layer("chest pain", data)
        self.assertEqual(out["urgency_level"], "EMERGENCY")

    def test_low_confidence_warning(self):
        data = {
            "urgency_level": "URGENT",
            "confidence": 0.5,
            "reasoning": "Symptoms unclear.",
            "red_flags": [],
            "care_pathway": "CHC",
        }
        out = self.service._apply_safety_layer("fever", data)
        self.assertIn("seek urgent care", out["reasoning"].lower())

    def test_rule_based_fallback(self):
        result = asyncio.run(self.service.fallback_rule_based("fever"))
        self.assertIn("urgency_level", result)


if __name__ == "__main__":
    unittest.main()
