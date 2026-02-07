from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.follow_up import (
    FollowUpPublic,
    FollowUpReminderResponse,
    FollowUpResponsePayload,
)
from app.services.followup_reminder_service import FollowUpReminderService

router = APIRouter(prefix="/followups", tags=["followups"])


@router.get("/{token}", response_model=FollowUpPublic)
async def get_followup(token: str, session: AsyncSession = Depends(get_session)):
    service = FollowUpReminderService(session)
    reminder = await service.get_by_token(token)
    if not reminder:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    from sqlalchemy import text
    stmt = text(
        "SELECT r.token, r.urgency_level, r.scheduled_time, r.sent_at, r.response_status, "
        "t.reasoning, t.care_pathway "
        "FROM follow_up_reminders r "
        "JOIN triage_sessions t ON t.id = r.triage_session_id "
        "WHERE r.token = :token LIMIT 1"
    )
    result = await session.execute(stmt, {"token": token})
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return {
        "token": row["token"],
        "urgency_level": row["urgency_level"],
        "scheduled_time": row["scheduled_time"],
        "sent_at": row["sent_at"],
        "response_status": row["response_status"],
        "triage_reasoning": row["reasoning"],
        "care_pathway": row["care_pathway"],
    }


@router.post("/{token}/respond", response_model=FollowUpReminderResponse)
async def respond_followup(
    token: str,
    payload: FollowUpResponsePayload,
    session: AsyncSession = Depends(get_session),
):
    service = FollowUpReminderService(session)
    reminder = await service.record_response(
        token=token,
        status=payload.response_status,
        new_symptoms=payload.new_symptoms,
        need_help=payload.need_help,
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return reminder
