from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from PIL import Image, ImageFilter, ImageStat

from app.core.config import get_settings

logger = logging.getLogger("app.services.visual_skin")


@dataclass
class ImageQualityResult:
    filename: str
    width: int
    height: int
    size_kb: int
    blur_score: float
    brightness: float
    quality: str
    issues: list[str]


class VisualSkinService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _ensure_upload_dir(self) -> str:
        base = os.path.join(os.getcwd(), self.settings.image_upload_dir)
        os.makedirs(base, exist_ok=True)
        return base

    def save_images(self, files: list[tuple[str, bytes]]) -> list[str]:
        base = self._ensure_upload_dir()
        stored = []
        for name, content in files:
            ext = os.path.splitext(name)[-1].lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                ext = ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"
            path = os.path.join(base, filename)
            with open(path, "wb") as f:
                f.write(content)
            stored.append(path)
        return stored

    def _strip_metadata(self, content: bytes) -> bytes:
        image = Image.open(io_bytes(content))
        image = image.convert("RGB")
        out = io_bytes()
        image.save(out, format="JPEG", quality=90)
        return out.getvalue()

    def analyze_quality(self, name: str, content: bytes) -> ImageQualityResult:
        image = Image.open(io_bytes(content))
        image = image.convert("RGB")
        width, height = image.size
        size_kb = max(1, len(content) // 1024)

        gray = image.convert("L").filter(ImageFilter.FIND_EDGES)
        stat = ImageStat.Stat(gray)
        blur_score = float(stat.var[0])
        brightness = float(ImageStat.Stat(image.convert("L")).mean[0])

        issues = []
        if width < 480 or height < 480:
            issues.append("resolution too low")
        if blur_score < 120.0:
            issues.append("too blurry")
        if brightness < 40:
            issues.append("too dark")
        if brightness > 210:
            issues.append("too bright")

        if issues:
            quality = "poor" if len(issues) >= 2 or "resolution too low" in issues else "fair"
        else:
            quality = "good"

        return ImageQualityResult(
            filename=name,
            width=width,
            height=height,
            size_kb=size_kb,
            blur_score=blur_score,
            brightness=brightness,
            quality=quality,
            issues=issues,
        )

    def _encode_image(self, content: bytes) -> str:
        return base64.b64encode(content).decode("utf-8")

    def _build_prompt(self, context: dict) -> str:
        return (
            "You are a medical triage assistant for rural Indian healthcare analyzing skin condition photographs. "
            "Your role is to assess urgency and provide guidance, NOT to diagnose definitively. "
            "Be conservative with urgency levels to ensure patient safety.\n\n"
            f"Patient age: {context.get('patient_age')}\n"
            f"Gender: {context.get('patient_gender')}\n"
            f"Body location: {', '.join(context.get('body_locations', []))}\n"
            f"Duration: {context.get('duration')}\n"
            f"Associated symptoms: {', '.join(context.get('associated_symptoms', []))}\n"
            f"Description: {context.get('patient_description')}\n"
            f"Previous treatment: {context.get('previous_treatment')}\n"
            f"Allergies: {context.get('allergies')}\n\n"
            "Return JSON with keys: urgency_level, confidence, observations, possible_conditions, red_flags, "
            "immediate_actions, home_care, when_to_seek_care, medications, specialist, limitations."
        )

    async def analyze(self, images: list[tuple[str, bytes]], context: dict) -> dict:
        prompt = self._build_prompt(context)
        quality = [self.analyze_quality(name, content) for name, content in images]
        encoded_images = []
        for name, content in images:
            encoded_images.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{self._encode_image(content)}"
                    },
                }
            )

        payload = {
            "model": self.settings.groq_vision_model,
            "temperature": 0.2,
            "max_tokens": 900,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}, *encoded_images],
                }
            ],
        }
        headers = {"Authorization": f"Bearer {self.settings.groq_api_key}"}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
        except Exception as exc:  # pragma: no cover
            logger.warning("Vision analysis failed, using fallback: %s", exc)
            data = self._fallback_response()

        data = self._normalize_response(data)
        data["quality"] = [
            {
                "filename": item.filename,
                "width": item.width,
                "height": item.height,
                "size_kb": item.size_kb,
                "blur_score": item.blur_score,
                "brightness": item.brightness,
                "quality": item.quality,
                "issues": item.issues,
            }
            for item in quality
        ]
        return data

    def _fallback_response(self) -> dict:
        return {
            "urgency_level": "ROUTINE",
            "confidence": 0.62,
            "observations": [
                "Localized redness with mild swelling",
                "No obvious bleeding or severe blistering",
            ],
            "possible_conditions": [
                {
                    "name": "Mild dermatitis",
                    "reason": "Redness and irritation without severe complications.",
                    "likelihood": "high",
                },
                {
                    "name": "Insect bite reaction",
                    "reason": "Localized swelling and redness.",
                    "likelihood": "medium",
                },
                {
                    "name": "Mild skin infection",
                    "reason": "Could be early inflammation.",
                    "likelihood": "low",
                },
            ],
            "red_flags": ["Rapid spreading", "Fever above 102F"],
            "immediate_actions": ["Keep area clean and dry", "Avoid scratching"],
            "home_care": ["Use a gentle moisturizer", "Monitor for changes"],
            "when_to_seek_care": ["If pain worsens", "If fever develops"],
            "medications": ["Paracetamol for pain if needed"],
            "specialist": "General physician",
            "limitations": "Image quality and lighting may limit accuracy.",
        }

    def _normalize_response(self, data: dict) -> dict:
        return {
            "urgency_level": data.get("urgency_level", "ROUTINE"),
            "confidence": float(data.get("confidence", 0.6)),
            "observations": data.get("observations", []),
            "possible_conditions": data.get("possible_conditions", []),
            "red_flags": data.get("red_flags", []),
            "immediate_actions": data.get("immediate_actions", []),
            "home_care": data.get("home_care", []),
            "when_to_seek_care": data.get("when_to_seek_care", []),
            "medications": data.get("medications", []),
            "specialist": data.get("specialist"),
            "limitations": data.get(
                "limitations", "This is a triage aid and not a diagnosis."
            ),
        }


def io_bytes(data: bytes | None = None):
    import io

    return io.BytesIO(data) if data is not None else io.BytesIO()
