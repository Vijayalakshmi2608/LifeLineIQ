from fastapi import APIRouter, Depends

from app.core.database import get_session
from app.schemas.outbreak import OutbreakList
from app.schemas.follow_up import FollowUpMetrics
from app.services.followup_reminder_service import calculate_followup_metrics
from app.services.outbreak_service import OutbreakService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/outbreaks", response_model=OutbreakList)
async def list_outbreaks(
    radius_km: int = 5,
    window_hours: int = 48,
    min_cases: int = 15,
    session=Depends(get_session),
):
    service = OutbreakService(session)
    outbreaks = await service.get_active_outbreaks(
        radius_km=radius_km, window_hours=window_hours, min_cases=min_cases
    )
    return {"outbreaks": outbreaks}


@router.get("/followups/metrics", response_model=FollowUpMetrics)
async def followup_metrics(session=Depends(get_session)):
    metrics = await calculate_followup_metrics(session)
    return metrics
