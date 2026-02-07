from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image


@dataclass
class VisualAnalysisResult:
    urgency_level: str
    confidence_score: float
    findings: list[dict]


class VisualAnalysisService:
    def analyze(self, image_bytes: bytes) -> VisualAnalysisResult:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((256, 256))
        pixels = list(image.getdata())
        if not pixels:
            return VisualAnalysisResult(
                urgency_level="ROUTINE",
                confidence_score=0.4,
                findings=[
                    {
                        "title": "Image unreadable",
                        "detail": "We couldn't analyze the image clearly.",
                        "severity": "medium",
                    }
                ],
            )

        avg_r = sum(p[0] for p in pixels) / len(pixels)
        avg_g = sum(p[1] for p in pixels) / len(pixels)
        avg_b = sum(p[2] for p in pixels) / len(pixels)
        redness_ratio = avg_r / max(1.0, (avg_g + avg_b) / 2)

        severity = "low"
        urgency = "ROUTINE"
        confidence = 0.7
        detail = "No obvious high-risk visual patterns detected."

        if redness_ratio > 1.25:
            severity = "medium"
            urgency = "URGENT"
            confidence = 0.82
            detail = "Noticeable redness detected. This can indicate inflammation or infection."
        if redness_ratio > 1.45:
            severity = "high"
            urgency = "EMERGENCY"
            confidence = 0.88
            detail = "Severe redness detected. Seek urgent care if pain or swelling worsens."

        findings = [
            {"title": "Visual Findings", "detail": detail, "severity": severity},
            {
                "title": "Confidence",
                "detail": f"{int(confidence * 100)}% match",
                "severity": "medium" if confidence < 0.85 else "low",
            },
            {
                "title": "Severity",
                "detail": "High risk" if severity == "high" else "Moderate" if severity == "medium" else "Low risk",
                "severity": severity,
            },
        ]

        return VisualAnalysisResult(
            urgency_level=urgency,
            confidence_score=confidence,
            findings=findings,
        )
