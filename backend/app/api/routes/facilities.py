from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.facility import FacilityList, FacilitySearch
from app.services.facility_service import FacilitySearchService

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.post("/search", response_model=FacilityList)
async def search_facilities(
    payload: FacilitySearch, session: AsyncSession = Depends(get_session)
):
    service = FacilitySearchService(session)
    return await service.find_nearest(
        user_lat=payload.user_lat,
        user_lng=payload.user_lng,
        urgency_level=payload.urgency_level,
        radius_km=payload.radius_km,
        max_results=payload.max_results,
        facility_types=payload.facility_types,
        open_now=payload.open_now,
        emergency_only=payload.emergency_only,
        max_wait_minutes=payload.max_wait_minutes,
    )
