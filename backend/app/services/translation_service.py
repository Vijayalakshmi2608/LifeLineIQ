from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self) -> None:
        self.enabled = False

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not self.enabled:
            return text
        if not text or source_lang == target_lang:
            return text
        return text
