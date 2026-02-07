from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.core.database import AsyncSessionFactory
from app.services.followup_reminder_service import FollowUpReminderService

logger = logging.getLogger(__name__)
settings = get_settings()


class FollowUpScheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone=settings.timezone)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.add_job(
            self._dispatch_job,
            IntervalTrigger(minutes=1),
            id="followup_dispatch",
            replace_existing=True,
        )
        self.scheduler.start()
        self._started = True
        logger.info("Follow-up scheduler started.")

    def shutdown(self) -> None:
        if not self._started:
            return
        self.scheduler.shutdown(wait=False)
        self._started = False
        logger.info("Follow-up scheduler stopped.")

    async def _dispatch_job(self) -> None:
        async with AsyncSessionFactory() as session:
            service = FollowUpReminderService(session)
            sent = await service.dispatch_due()
            if sent:
                logger.info("Follow-up reminders sent: %s", sent)


followup_scheduler = FollowUpScheduler()
