from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, facilities, followups, health, i18n, medications, triage, visual
from app.core.config import get_settings
from app.core.database import health_check, init_db
from app.core.security import RateLimiter, rate_limit_middleware, request_id_middleware
from app.services.followup_scheduler import followup_scheduler

settings = get_settings()
logger = logging.getLogger("app")

app = FastAPI(title="Rural Health Triage API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.computed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_id_middleware())
app.middleware("http")(rate_limit_middleware(RateLimiter()))

app.include_router(health.router)
app.include_router(triage.router)
app.include_router(facilities.router)
app.include_router(admin.router)
app.include_router(i18n.router)
app.include_router(followups.router)
app.include_router(medications.router)
app.include_router(visual.router)


@app.get("/")
async def root():
    return {"message": "Rural Health Triage API is running", "docs": "/docs"}


@app.on_event("startup")
async def startup_event():
    await init_db()
    if settings.skip_db_check:
        logger.warning("Skipping DB health check (SKIP_DB_CHECK=true).")
        followup_scheduler.start()
        return
    try:
        await init_db()
        await health_check()
        logger.info("Database connection verified.")
        followup_scheduler.start()
    except Exception as exc:  # pragma: no cover
        logger.exception("Database connection failed: %s", exc)


@app.on_event("shutdown")
async def shutdown_event():
    followup_scheduler.shutdown()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."},
        headers={"X-Request-ID": getattr(request.state, "request_id", "")},
    )
