from pydantic import BaseModel, ConfigDict


class VisualFinding(BaseModel):
    title: str
    detail: str
    severity: str


class VisualAnalysisResponse(BaseModel):
    urgency_level: str
    confidence_score: float
    findings: list[VisualFinding]
    reference_images: list[str] = []

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "urgency_level": "ROUTINE",
                    "confidence_score": 0.78,
                    "findings": [
                        {
                            "title": "Visual Findings",
                            "detail": "Mild redness detected.",
                            "severity": "low",
                        }
                    ],
                    "reference_images": [],
                }
            ]
        }
    )
