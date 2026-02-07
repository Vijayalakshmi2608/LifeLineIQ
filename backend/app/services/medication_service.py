from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import DrugInteraction, Medication, PatientMedication


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


class MedicationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, query: str, limit: int = 10) -> list[Medication]:
        if not query:
            return []
        q = f"%{query.lower()}%"
        stmt = (
            select(Medication)
            .where(Medication.is_active.is_(True))
            .where(
                (Medication.name.ilike(q))
                | (Medication.generic_name.ilike(q))
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        meds = list(result.scalars().all())
        if meds:
            return meds
        # Fallback on alias match
        stmt = select(Medication).where(Medication.is_active.is_(True))
        result = await self.session.execute(stmt)
        meds = []
        norm_query = _normalize(query)
        for med in result.scalars().all():
            for lang_name in (med.language_names or {}).values():
                if _normalize(str(lang_name)) == norm_query:
                    meds.append(med)
                    break
            for alias in med.aliases or []:
                if _normalize(alias) == norm_query:
                    meds.append(med)
                    break
        return meds[:limit]

    async def resolve_medication(self, name: str) -> Medication | None:
        if not name:
            return None
        meds = await self.search(name, limit=5)
        if meds:
            return meds[0]
        return None

    async def check_interactions(
        self, current: list[str], recommended: str
    ) -> tuple[list[dict], list[str]]:
        interactions = []
        unknown = []
        recommended_med = await self.resolve_medication(recommended)
        if not recommended_med:
            return [], [recommended]

        for med_name in current:
            current_med = await self.resolve_medication(med_name)
            if not current_med:
                unknown.append(med_name)
                continue
            stmt = select(DrugInteraction).where(
                ((DrugInteraction.drug1_id == current_med.id) & (DrugInteraction.drug2_id == recommended_med.id))
                | ((DrugInteraction.drug1_id == recommended_med.id) & (DrugInteraction.drug2_id == current_med.id))
            )
            result = await self.session.execute(stmt)
            interaction = result.scalars().first()
            if interaction:
                interactions.append(
                    {
                        "drug1": current_med.name,
                        "drug2": recommended_med.name,
                        "severity": interaction.severity,
                        "description": interaction.description,
                        "recommendation": interaction.recommendation,
                    }
                )
        return interactions, unknown

    async def add_patient_medication(
        self, patient_id: str, medication_name: str, dosage: str | None, frequency: str | None
    ) -> PatientMedication | None:
        med = await self.resolve_medication(medication_name)
        if not med:
            return None
        record = PatientMedication(
            patient_id=patient_id,
            medication_id=med.id,
            dosage=dosage,
            frequency=frequency,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_patient_medications(self, patient_id: str) -> list[dict]:
        stmt = select(PatientMedication, Medication).where(
            PatientMedication.patient_id == patient_id,
            PatientMedication.medication_id == Medication.id,
            PatientMedication.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        items = []
        for pm, med in result.all():
            items.append(
                {
                    "id": pm.id,
                    "patient_id": pm.patient_id,
                    "medication_name": med.name,
                    "dosage": pm.dosage,
                    "frequency": pm.frequency,
                    "is_active": pm.is_active,
                }
            )
        return items
