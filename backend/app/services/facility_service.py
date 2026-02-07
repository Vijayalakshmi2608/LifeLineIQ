from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class FacilitySearchService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def find_nearest(
        self,
        user_lat: float,
        user_lng: float,
        urgency_level: str,
        radius_km: int = 50,
        max_results: int = 5,
        facility_types: list[str] | None = None,
        open_now: bool | None = None,
        emergency_only: bool | None = None,
        max_wait_minutes: int | None = None,
    ) -> dict:
        facilities = await self._query_nearby(
            user_lat=user_lat,
            user_lng=user_lng,
            radius_km=radius_km,
            max_results=max_results * 2,
        )
        if not facilities:
            facilities = await self._fetch_overpass(
                user_lat=user_lat, user_lng=user_lng, radius_km=radius_km
            )

        filtered = self.filter_by_urgency(
            facilities,
            urgency_level,
            facility_types=facility_types,
            open_now=open_now,
            emergency_only=emergency_only,
            max_wait_minutes=max_wait_minutes,
        )

        enriched = []
        for facility in filtered[:max_results]:
            enriched_facility = await self.enrich_facility_data(
                facility, user_lat=user_lat, user_lng=user_lng, urgency=urgency_level
            )
            enriched.append(enriched_facility)

        return {
            "facilities": enriched,
            "total_found": len(facilities),
            "search_radius": radius_km,
            "user_location": {"lat": user_lat, "lng": user_lng},
        }

    async def _query_nearby(
        self, user_lat: float, user_lng: float, radius_km: int, max_results: int
    ) -> list[dict]:
        sql = text(
            """
            SELECT *,
                   (6371 * acos(
                       cos(radians(:user_lat)) *
                       cos(radians(latitude)) *
                       cos(radians(longitude) - radians(:user_lng)) +
                       sin(radians(:user_lat)) *
                       sin(radians(latitude))
                   )) AS distance_km
            FROM facilities
            WHERE is_active = true
            AND (6371 * acos(
                cos(radians(:user_lat)) *
                cos(radians(latitude)) *
                cos(radians(longitude) - radians(:user_lng)) +
                sin(radians(:user_lat)) *
                sin(radians(latitude))
            )) <= :radius_km
            ORDER BY distance_km ASC
            LIMIT :max_results
            """
        )
        result = await self.db.execute(
            sql,
            {
                "user_lat": user_lat,
                "user_lng": user_lng,
                "radius_km": radius_km,
                "max_results": max_results,
            },
        )
        return [dict(row) for row in result.mappings().all()]

    def filter_by_urgency(
        self,
        facilities: list[dict],
        urgency: str,
        facility_types: list[str] | None = None,
        open_now: bool | None = None,
        emergency_only: bool | None = None,
        max_wait_minutes: int | None = None,
    ) -> list[dict]:
        filtered = facilities
        if emergency_only or urgency == "EMERGENCY":
            filtered = [f for f in filtered if f.get("emergency_available")]
        if urgency == "URGENT":
            filtered = [f for f in filtered if self.is_open_now(f) is not False]
        if open_now is True:
            filtered = [f for f in filtered if self.is_open_now(f) is True]
        if facility_types:
            types = {t.upper() for t in facility_types}
            filtered = [f for f in filtered if str(f.get("facility_type", "")).upper() in types]
        if max_wait_minutes is not None:
            filtered = [
                f
                for f in filtered
                if (f.get("estimated_wait_time") or 0) <= max_wait_minutes
            ]
        return filtered

    async def enrich_facility_data(
        self, facility: dict, user_lat: float, user_lng: float, urgency: str
    ) -> dict:
        distance = float(facility.get("distance_km", 0))
        travel_time_mins = max(
            1, int((distance / self._average_speed_kmh(facility, urgency)) * 60)
        )
        is_open, opens_at = self.check_operating_hours(facility.get("operating_hours"))

        google_maps_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={user_lat},{user_lng}"
            f"&destination={facility['latitude']},{facility['longitude']}"
            "&travelmode=driving"
        )
        call_url = f"tel:{facility.get('contact_number')}"
        wait_time_indicator = self.get_wait_time_indicator(
            facility.get("estimated_wait_time", 30)
        )

        return {
            "id": str(facility["id"]),
            "name": facility["name"],
            "facility_type": facility["facility_type"],
            "latitude": float(facility["latitude"]),
            "longitude": float(facility["longitude"]),
            "distance_km": round(distance, 1),
            "travel_time_mins": travel_time_mins,
            "travel_time": travel_time_mins,
            "address": facility["address"],
            "district": facility.get("district", "") or "",
            "state": facility.get("state", "") or "",
            "pincode": facility.get("pincode", "") or "",
            "contact_number": facility["contact_number"],
            "is_open_now": is_open,
            "opens_at": opens_at,
            "wait_time": wait_time_indicator,
            "emergency_available": facility["emergency_available"],
            "specialties": facility.get("specialties") or [],
            "bed_capacity": facility.get("bed_capacity"),
            "estimated_wait_time": facility.get("estimated_wait_time", 30),
            "operating_hours": facility.get("operating_hours"),
            "is_active": bool(facility.get("is_active", True)),
            "last_updated": facility.get("last_updated"),
            "directions_url": google_maps_url,
            "call_url": call_url,
        }

    def get_wait_time_indicator(self, minutes: int) -> dict:
        if minutes < 15:
            return {"level": "low", "text": "Low wait", "color": "green"}
        if minutes < 45:
            return {"level": "medium", "text": "Medium wait", "color": "yellow"}
        return {"level": "high", "text": "High wait", "color": "red"}

    def check_operating_hours(
        self, hours_json: dict | None
    ) -> tuple[bool | None, str | None]:
        now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        current_day = now.strftime("%A").lower()
        current_time = now.time()

        if not hours_json:
            return None, None
        if hours_json.get("24/7"):
            return True, None

        today_hours = hours_json.get(current_day)
        if not today_hours:
            return False, "Closed today"

        open_time, close_time = today_hours.split("-")
        open_hour = datetime.strptime(open_time, "%H:%M").time()
        close_hour = datetime.strptime(close_time, "%H:%M").time()

        if open_hour <= current_time <= close_hour:
            return True, None
        if current_time < open_hour:
            return False, f"Opens at {open_time}"
        return False, "Closed now"

    def is_open_now(self, facility: dict) -> bool | None:
        is_open, _ = self.check_operating_hours(facility.get("operating_hours"))
        return is_open

    def _average_speed_kmh(self, facility: dict, urgency: str) -> float:
        if urgency == "EMERGENCY":
            return 50
        if facility.get("emergency_available"):
            return 45
        return 35

    async def _fetch_overpass(
        self, user_lat: float, user_lng: float, radius_km: int
    ) -> list[dict]:
        radius_m = int(radius_km * 1000)
        query = f"""
        [out:json][timeout:10];
        (
          node["amenity"~"hospital|clinic|doctors|health_centre"](around:{radius_m},{user_lat},{user_lng});
          way["amenity"~"hospital|clinic|doctors|health_centre"](around:{radius_m},{user_lat},{user_lng});
          relation["amenity"~"hospital|clinic|doctors|health_centre"](around:{radius_m},{user_lat},{user_lng});
        );
        out center tags;
        """
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                resp = await client.post(
                    "https://overpass-api.de/api/interpreter",
                    content=query,
                    headers={"Content-Type": "text/plain"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return []

        facilities = []
        for element in data.get("elements", []):
            lat = element.get("lat") or element.get("center", {}).get("lat")
            lng = element.get("lon") or element.get("center", {}).get("lon")
            if lat is None or lng is None:
                continue
            tags = element.get("tags") or {}
            facility_type = self._map_amenity(tags.get("amenity", ""))
            distance = self._haversine_km(user_lat, user_lng, lat, lng)
            facilities.append(
                {
                    "id": f"osm-{element.get('id')}",
                    "name": tags.get("name") or "Health Facility",
                    "facility_type": facility_type,
                    "latitude": lat,
                    "longitude": lng,
                    "address": tags.get("addr:street") or tags.get("addr:full") or "Address unavailable",
                    "district": tags.get("addr:district") or tags.get("addr:city") or "",
                    "state": tags.get("addr:state") or "",
                    "pincode": tags.get("addr:postcode") or "",
                    "contact_number": tags.get("phone") or tags.get("contact:phone") or "",
                    "emergency_available": facility_type in {"DH", "MEDICAL_COLLEGE"},
                    "operating_hours": {"24/7": True} if "24/7" in (tags.get("opening_hours") or "") else None,
                    "specialties": [tags.get("healthcare")] if tags.get("healthcare") else [],
                    "bed_capacity": None,
                    "estimated_wait_time": 30,
                    "is_active": True,
                    "last_updated": None,
                    "distance_km": distance,
                }
            )
        return facilities

    def _map_amenity(self, amenity: str) -> str:
        if amenity == "hospital":
            return "DH"
        if amenity in {"clinic", "health_centre"}:
            return "CHC"
        return "PHC"

    def _haversine_km(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
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
