from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/i18n", tags=["i18n"])


@router.post("/translate")
async def translate_text(
    text: str = Form(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
):
    service = TranslationService()
    translated = service.translate(text, source_lang, target_lang)
    return {
        "original": text,
        "translated": translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }


@router.post("/voice-to-text")
async def voice_to_text(
    audio: UploadFile = File(...),
    language: str = Form(...),
):
    try:
        service = VoiceService()
        content = await audio.read()
        result = service.transcribe(content, language=language)
        return {
            "text": result.text,
            "language": result.language,
            "confidence": result.confidence,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    language: str = Form(...),
):
    try:
        from gtts import gTTS  # type: ignore
        import io

        tts = gTTS(text=text, lang=language)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return StreamingResponse(fp, media_type="audio/mpeg")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=str(exc)) from exc
