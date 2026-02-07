from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.database import health_check

router = APIRouter()


@router.get("/health")
async def health():
    try:
        await health_check()
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=200,
            content={"status": "degraded", "database": "unreachable"},
        )
