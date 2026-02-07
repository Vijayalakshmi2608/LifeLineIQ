from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.follow_up import FollowUpReminder
from app.models.triage import TriageSession
from app.models.patient import Patient
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)
settings = get_settings()


class FollowUpReminderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.translator = TranslationService()

    def _next_followup_time(self, urgency_level: str) -> datetime | None:
        now = datetime.now(timezone.utc)
        if urgency_level == "EMERGENCY":
            return None
        if urgency_level == "URGENT":
            return now + timedelta(hours=4)
        if urgency_level == "ROUTINE":
            return now + timedelta(hours=24)
        return now + timedelta(hours=48)

    async def schedule_from_triage(
        self,
        patient_id: str,
        triage_session_id: str,
        urgency_level: str,
        language: str,
    ) -> FollowUpReminder | None:
        scheduled_time = self._next_followup_time(urgency_level)
        if not scheduled_time:
            return None
        if not patient_id or patient_id == "anonymous":
            return None

        patient = await self.session.get(Patient, patient_id)
        if not patient or patient.opted_out:
            return None

        token = uuid.uuid4().hex
        deep_link_base = settings.public_app_url or settings.frontend_url
        deep_link = f"{deep_link_base.rstrip('/')}/followup/{token}"

        reminder = FollowUpReminder(
            token=token,
            patient_id=patient_id,
            triage_session_id=triage_session_id,
            urgency_level=urgency_level,
            scheduled_time=scheduled_time,
            deep_link=deep_link,
            message_language=language,
        )
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def get_due_reminders(self) -> list[FollowUpReminder]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(FollowUpReminder)
            .where(FollowUpReminder.sent_at.is_(None))
            .where(FollowUpReminder.scheduled_time <= now)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _should_skip(self, reminder: FollowUpReminder) -> tuple[bool, str | None]:
        patient = await self.session.get(Patient, reminder.patient_id)
        if not patient or patient.opted_out:
            return True, "opted_out"

        # Skip if new triage started after scheduled time.
        stmt = (
            select(TriageSession.id)
            .where(TriageSession.patient_id == reminder.patient_id)
            .where(TriageSession.created_at > reminder.scheduled_time)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none():
            return True, "new_triage"

        triage = await self.session.get(TriageSession, reminder.triage_session_id)
        if triage and triage.visited_hospital:
            return True, "visited_hospital"
        return False, None

    async def dispatch_due(self) -> int:
        due = await self.get_due_reminders()
        if not due:
            return 0
        sent_count = 0
        for reminder in due:
            skip, reason = await self._should_skip(reminder)
            if skip:
                reminder.sent_at = datetime.now(timezone.utc)
                reminder.response_status = "skipped"
                await self.session.commit()
                logger.info("Follow-up skipped (%s) for %s", reason, reminder.id)
                continue

            patient = await self.session.get(Patient, reminder.patient_id)
            if not patient:
                continue

            message = self._build_message(reminder, patient)
            delivered = await self._send_message(patient.phone_number, message)
            if delivered:
                reminder.sent_at = datetime.now(timezone.utc)
                reminder.channel = delivered
                await self.session.commit()
                sent_count += 1
        return sent_count

    def _build_message(self, reminder: FollowUpReminder, patient: Patient) -> str:
        base = (
            "Hello! It's time for a quick check-in.\n\n"
            "How are your symptoms now?\n"
            "1) Better\n2) Same\n3) Worse\n\n"
            f"Reply here: {reminder.deep_link}"
        )
        if reminder.message_language and reminder.message_language != "en":
            return self.translator.translate(base, "en", reminder.message_language)
        return base

    async def _send_message(self, phone_number: str, message: str) -> str | None:
        if not phone_number:
            logger.warning("No phone number, skipping follow-up message.")
            return None
        if settings.twilio_account_sid and settings.twilio_auth_token:
            try:
                from twilio.rest import Client

                client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
                if settings.twilio_whatsapp_from:
                    client.messages.create(
                        from_=settings.twilio_whatsapp_from,
                        to=f"whatsapp:{phone_number}",
                        body=message,
                    )
                    return "whatsapp"
                if settings.twilio_sms_from:
                    client.messages.create(
                        from_=settings.twilio_sms_from, to=phone_number, body=message
                    )
                    return "sms"
            except Exception as exc:
                logger.error("Twilio send failed: %s", exc)
                return None
        logger.info("Follow-up message (simulated) to %s: %s", phone_number, message)
        return "simulated"

    async def record_response(
        self, token: str, status: str, new_symptoms: str | None, need_help: bool | None
    ) -> FollowUpReminder | None:
        stmt = select(FollowUpReminder).where(FollowUpReminder.token == token)
        result = await self.session.execute(stmt)
        reminder = result.scalar_one_or_none()
        if not reminder:
            return None

        reminder.response_status = status
        reminder.response_received_at = datetime.now(timezone.utc)

        if status == "worse":
            reminder.escalated = True
            await self._notify_asha_worker(reminder, new_symptoms, need_help)
        await self.session.commit()
        return reminder

    async def get_by_token(self, token: str) -> FollowUpReminder | None:
        stmt = select(FollowUpReminder).where(FollowUpReminder.token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _notify_asha_worker(
        self, reminder: FollowUpReminder, new_symptoms: str | None, need_help: bool | None
    ) -> None:
        if not settings.asha_worker_number:
            return
        message = (
            "Patient follow-up indicates worsening symptoms.\n"
            f"Follow-up token: {reminder.token}\n"
            f"New symptoms: {new_symptoms or 'Not provided'}\n"
            f"Needs immediate help: {'Yes' if need_help else 'No'}\n"
            f"Link: {reminder.deep_link}"
        )
        await self._send_message(settings.asha_worker_number, message)


async def calculate_followup_metrics(session: AsyncSession) -> dict:
    total_sent = await session.scalar(
        select(text("count(*)")).select_from(FollowUpReminder).where(
            FollowUpReminder.sent_at.is_not(None)
        )
    )
    total_responded = await session.scalar(
        select(text("count(*)")).select_from(FollowUpReminder).where(
            FollowUpReminder.response_received_at.is_not(None)
        )
    )
    improved = await session.scalar(
        select(text("count(*)")).select_from(FollowUpReminder).where(
            FollowUpReminder.response_status == "better"
        )
    )
    same = await session.scalar(
        select(text("count(*)")).select_from(FollowUpReminder).where(
            FollowUpReminder.response_status == "same"
        )
    )
    worse = await session.scalar(
        select(text("count(*)")).select_from(FollowUpReminder).where(
            FollowUpReminder.response_status == "worse"
        )
    )
    total_sent = total_sent or 0
    total_responded = total_responded or 0
    improved = improved or 0
    same = same or 0
    worse = worse or 0
    response_rate = (total_responded / total_sent) if total_sent else 0.0
    return {
        "total_sent": total_sent,
        "total_responded": total_responded,
        "improved": improved,
        "same": same,
        "worse": worse,
        "response_rate": round(response_rate, 3),
    }
