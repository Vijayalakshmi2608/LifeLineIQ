from __future__ import annotations

import io
import logging
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float


class VoiceService:
    def __init__(self) -> None:
        try:
            import whisper  # type: ignore

            self._model = whisper.load_model("base")
        except Exception as exc:  # pragma: no cover
            logger.warning("Whisper not available: %s", exc)
            self._model = None

    def transcribe(self, audio_bytes: bytes, language: str) -> TranscriptionResult:
        if self._model is None:
            raise RuntimeError("Whisper model not available")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            result = self._model.transcribe(tmp.name, language=language)
        return TranscriptionResult(
            text=result.get("text", "").strip(),
            language=language,
            confidence=float(result.get("confidence", 1.0)),
        )
