from __future__ import annotations

import re
import time
import uuid
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response


def sanitize_input(value: str) -> str:
    cleaned = re.sub(r"[;<>$`]", "", value)
    return cleaned.strip()


class RateLimiter:
    def __init__(self, limit: int = 100, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        bucket = self.hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True


def request_id_middleware() -> Callable:
    async def middleware(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    return middleware


def rate_limit_middleware(limiter: RateLimiter) -> Callable:
    async def middleware(request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        if not limiter.allow(client_ip):
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"},
            )
        return await call_next(request)

    return middleware
