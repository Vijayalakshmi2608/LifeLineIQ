from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionFactory, init_db
from app.models.medication import DrugInteraction, Medication


MEDICATIONS = [
    # name, generic, category, aliases
    ("Paracetamol", "Acetaminophen", "Pain reliever", ["Crocin", "Dolo 650", "Calpol"]),
    ("Ibuprofen", "Ibuprofen", "NSAID", ["Brufen", "Ibugesic"]),
    ("Aspirin", "Aspirin", "Antiplatelet", []),
    ("Metformin", "Metformin", "Diabetes medication", ["Glycomet"]),
    ("Amoxicillin", "Amoxicillin", "Antibiotic", ["Mox"]),
    ("Azithromycin", "Azithromycin", "Antibiotic", ["Azee"]),
    ("Cetirizine", "Cetirizine", "Antihistamine", ["Cetzine"]),
    ("Pantoprazole", "Pantoprazole", "PPI", ["Pantocid"]),
    ("Omeprazole", "Omeprazole", "PPI", ["Omez"]),
    ("Atorvastatin", "Atorvastatin", "Statin", ["Lipitor"]),
    ("Amlodipine", "Amlodipine", "BP medication", ["Amlong"]),
    ("Losartan", "Losartan", "BP medication", ["Losar"]),
    ("Metoprolol", "Metoprolol", "BP medication", ["Betaloc"]),
    ("Levothyroxine", "Levothyroxine", "Thyroid", ["Eltroxin"]),
    ("Insulin", "Insulin", "Diabetes medication", []),
]

# NOTE:
# This seed list is intentionally minimal. For real clinical use, load a validated
# interactions dataset (e.g., licensed sources). This demo data is NOT exhaustive.

INTERACTIONS = [
    # (drug1_generic, drug2_generic, severity, description, recommendation)
    (
        "Aspirin",
        "Ibuprofen",
        "SEVERE",
        "Both are NSAIDs. Taking together increases risk of stomach bleeding and ulcers.",
        "Avoid taking together. Use one or the other, not both.",
    ),
    (
        "Ibuprofen",
        "Metformin",
        "MINOR",
        "NSAIDs can affect kidney function, which may impact diabetes control.",
        "Stay hydrated and consult your clinician if you notice changes.",
    ),
]


async def seed() -> None:
    await init_db()
    async with AsyncSessionFactory() as session:
        existing = await session.execute(select(Medication))
        if existing.scalars().first():
            print("Medications already seeded.")
            return

        meds = {}
        for name, generic, category, aliases in MEDICATIONS:
            med = Medication(
                name=name,
                generic_name=generic,
                category=category,
                aliases=aliases,
                language_names={},
            )
            session.add(med)
            meds[generic] = med

        await session.commit()
        for generic, med in meds.items():
            await session.refresh(med)

        for drug1, drug2, severity, desc, rec in INTERACTIONS:
            d1 = meds.get(drug1)
            d2 = meds.get(drug2)
            if not (d1 and d2):
                continue
            session.add(
                DrugInteraction(
                    drug1_id=d1.id,
                    drug2_id=d2.id,
                    severity=severity,
                    description=desc,
                    recommendation=rec,
                )
            )
        await session.commit()
        print("Seeded medications and interactions.")


if __name__ == "__main__":
    asyncio.run(seed())
