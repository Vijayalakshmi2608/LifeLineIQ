import asyncio

from app.core.database import AsyncSessionFactory, init_db
from app.models.symptom_translation import SymptomTranslation


SEED = [
    ("hi", "पेट दर्द", "stomach pain"),
    ("hi", "ज्वर", "fever"),
    ("hi", "बुखार", "fever"),
    ("ta", "வயிற்று வலி", "stomach pain"),
    ("ta", "காய்ச்சல்", "fever"),
    ("te", "కడుపు నొప్పి", "stomach pain"),
    ("te", "జ్వరం", "fever"),
    ("kn", "ಹೊಟ್ಟೆ ನೋವು", "stomach pain"),
    ("kn", "ಜ್ವರ", "fever"),
    ("ml", "വയറുവേദന", "stomach pain"),
    ("ml", "ജ്വരം", "fever"),
    ("mr", "पोटदुखी", "stomach pain"),
    ("mr", "ताप", "fever"),
    ("bn", "পেট ব্যথা", "stomach pain"),
    ("bn", "জ্বর", "fever"),
    ("gu", "પેટનો દુખાવો", "stomach pain"),
    ("gu", "તાવ", "fever"),
    ("pa", "ਪੇਟ ਦਰਦ", "stomach pain"),
    ("pa", "ਬੁਖਾਰ", "fever"),
    ("or", "ପେଟ ଯନ୍ତ୍ରଣା", "stomach pain"),
    ("or", "ଜ୍ୱର", "fever"),
]


async def main():
    await init_db()
    async with AsyncSessionFactory() as session:
        for lang, local_term, standard_term in SEED:
            session.add(
                SymptomTranslation(
                    language_code=lang,
                    local_term=local_term,
                    standard_term=standard_term,
                )
            )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
