from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbreak import OutbreakEvent

SYMPTOM_CLUSTERS = [
    {"fever", "vomiting"},
    {"fever", "diarrhea"},
    {"cough", "fever"},
    {"rash", "fever"},
]


class OutbreakService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(self, lat: float, lng: float, symptoms: str) -> None:
        tokens = self._tokenize(symptoms)
        event = OutbreakEvent(
            lat=lat,
            lng=lng,
            symptoms_text=symptoms[:500],
            symptoms_tokens=list(tokens),
        )
        self.db.add(event)
        await self.db.commit()

    async def detect_outbreak(
        self,
        lat: float,
        lng: float,
        symptoms: str,
        radius_km: int = 5,
        window_hours: int = 48,
        min_cases: int = 15,
        similarity_threshold: float = 0.45,
    ) -> dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        lat_delta = radius_km / 111
        lng_delta = radius_km / max(1, 111 * math.cos(math.radians(lat)))

        stmt = select(OutbreakEvent).where(
            and_(
                OutbreakEvent.created_at >= cutoff,
                OutbreakEvent.lat.between(lat - lat_delta, lat + lat_delta),
                OutbreakEvent.lng.between(lng - lng_delta, lng + lng_delta),
            )
        )
        rows = (await self.db.execute(stmt)).scalars().all()

        target_tokens = self._tokenize(symptoms)
        matches = []
        for row in rows:
            dist = self._distance_km(lat, lng, row.lat, row.lng)
            if dist > radius_km:
                continue
            similarity = self._symptom_similarity(target_tokens, set(row.symptoms_tokens))
            if similarity >= similarity_threshold:
                matches.append(row)

        if len(matches) >= min_cases:
            return {
                "outbreak_detected": True,
                "radius_km": radius_km,
                "cases": len(matches),
                "window_hours": window_hours,
                "alert_message": "Possible localized outbreak detected in your area.",
                "recommended_action": "Notify local health officer and increase monitoring.",
                "symptom_cluster": list(target_tokens),
            }
        return {"outbreak_detected": False}

    async def get_active_outbreaks(
        self,
        radius_km: int = 5,
        window_hours: int = 48,
        min_cases: int = 15,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        stmt = select(OutbreakEvent).where(OutbreakEvent.created_at >= cutoff)
        rows = (await self.db.execute(stmt)).scalars().all()

        buckets: dict[str, list[OutbreakEvent]] = {}
        for row in rows:
            key = f"{round(row.lat, 2)}:{round(row.lng, 2)}"
            buckets.setdefault(key, []).append(row)

        outbreaks: list[dict[str, Any]] = []
        for items in buckets.values():
            if len(items) < min_cases:
                continue
            center_lat = sum(item.lat for item in items) / len(items)
            center_lng = sum(item.lng for item in items) / len(items)
            token_counts = Counter()
            for item in items:
                token_counts.update(item.symptoms_tokens)
            top_tokens = [token for token, _ in token_counts.most_common(5)]

            outbreaks.append(
                {
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "cases": len(items),
                    "radius_km": radius_km,
                    "window_hours": window_hours,
                    "top_symptoms": top_tokens,
                }
            )

        return outbreaks

    def _tokenize(self, symptoms: str) -> set[str]:
        text = symptoms.lower().replace(",", " ").replace("|", " ")
        tokens = {token.strip() for token in text.split() if token.strip()}
        return tokens

    def _symptom_similarity(self, a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        intersection = len(a & b)
        union = len(a | b)
        jaccard = intersection / union
        cluster_match = 0.0
        for cluster in SYMPTOM_CLUSTERS:
            if cluster.issubset(a) and cluster.issubset(b):
                cluster_match = 1.0
                break
        return 0.7 * jaccard + 0.3 * cluster_match

    def _distance_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        r = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        return 2 * r * math.asin(math.sqrt(a))
