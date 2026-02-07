from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import Base

settings = get_settings()

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {"ssl": True}
    engine_kwargs.update({"pool_size": 5, "max_overflow": 15, "pool_timeout": 30})

engine = create_async_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

AsyncSessionFactory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


async def health_check(retries: int = 3, base_delay: float = 0.5) -> bool:
    attempt = 0
    while True:
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except Exception:
            attempt += 1
            if attempt > retries:
                raise
            await asyncio.sleep(base_delay * attempt)


async def init_db() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
