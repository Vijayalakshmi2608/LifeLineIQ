from __future__ import annotations

import difflib
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.symptom_translation import SymptomTranslation

SYMPTOM_TRANSLATIONS = {
    "hi": {
        "पेट दर्द": "stomach pain",
        "ज्वर": "fever",
        "बुखार": "fever",
        "खांसी": "cough",
        "सांस फूलना": "shortness of breath",
    },
    "ta": {
        "வயிற்று வலி": "stomach pain",
        "காய்ச்சல்": "fever",
        "இருமல்": "cough",
        "மூச்சு திணறல்": "shortness of breath",
    },
    "te": {
        "కడుపు నొప్పి": "stomach pain",
        "జ్వరం": "fever",
        "దగ్గు": "cough",
        "శ్వాస తీసుకోవడంలో ఇబ్బంది": "shortness of breath",
    },
    "kn": {
        "ಹೊಟ್ಟೆ ನೋವು": "stomach pain",
        "ಜ್ವರ": "fever",
        "ಖಾಸಿ": "cough",
        "ಉಸಿರಾಟದ ತೊಂದರೆ": "shortness of breath",
    },
    "ml": {
        "വയറുവേദന": "stomach pain",
        "ജ്വരം": "fever",
        "ചുമ": "cough",
        "ശ്വാസം മുട്ടൽ": "shortness of breath",
    },
    "mr": {
        "पोटदुखी": "stomach pain",
        "ताप": "fever",
        "खोकला": "cough",
        "श्वास घेण्यात त्रास": "shortness of breath",
    },
    "bn": {
        "পেট ব্যথা": "stomach pain",
        "জ্বর": "fever",
        "কাশি": "cough",
        "শ্বাসকষ্ট": "shortness of breath",
    },
    "gu": {
        "પેટનો દુખાવો": "stomach pain",
        "તાવ": "fever",
        "ખાંસી": "cough",
        "શ્વાસ લેવામાં તકલીફ": "shortness of breath",
    },
    "pa": {
        "ਪੇਟ ਦਰਦ": "stomach pain",
        "ਬੁਖਾਰ": "fever",
        "ਖੰਘ": "cough",
        "ਸਾਹ ਲੈਣ ਵਿੱਚ ਦਿੱਕਤ": "shortness of breath",
    },
    "or": {
        "ପେଟ ଯନ୍ତ୍ରଣା": "stomach pain",
        "ଜ୍ୱର": "fever",
        "ଖାସି": "cough",
        "ଶ୍ୱାସକଷ୍ଟ": "shortness of breath",
    },
}


class SymptomMapper:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session

    async def map_terms(self, text: str, language: str) -> list[str]:
        if self.session is not None:
            db_terms = await self._db_map(text, language)
            if db_terms:
                return db_terms
        mapping = SYMPTOM_TRANSLATIONS.get(language, {})
        if not mapping:
            return [text]
        results = []
        for term, standard in mapping.items():
            if term in text:
                results.append(standard)
        if results:
            return results

        possibilities = list(mapping.keys())
        matches = difflib.get_close_matches(text, possibilities, n=1, cutoff=0.6)
        if matches:
            return [mapping[matches[0]]]

        return [text]

    async def _db_map(self, text: str, language: str) -> list[str]:
        if not text:
            return []
        stmt = select(SymptomTranslation).where(
            SymptomTranslation.language_code == language,
        )
        try:
            rows = (await self.session.execute(stmt)).scalars().all()
        except OperationalError:
            return []
        if not rows:
            return []
        for row in rows:
            if row.local_term in text:
                return [row.standard_term]
        possibilities = [row.local_term for row in rows]
        matches = difflib.get_close_matches(text, possibilities, n=1, cutoff=0.6)
        if matches:
            for row in rows:
                if row.local_term == matches[0]:
                    return [row.standard_term]
        return []
