"""Redis-based sliding window rate limiter middleware.

Enforces per-user submission limits using Redis sorted sets.
"""
import time
from fastapi import Request, HTTPException
from devascent.config import assessment_config


async def check_rate_limit(user_id: str, redis_client=None) -> bool:
    """Check if user has exceeded the submission rate limit.

    Uses Redis sorted set with sliding window. Falls back to
    always-allow if Redis is unavailable.

    Returns:
        True if rate limit is NOT exceeded (allowed to proceed)
    """
    if not redis_client:
        return True

    window_seconds = 3600  # 1 hour
    max_requests = assessment_config.max_submissions_per_hour
    now = time.time()
    window_start = now - window_seconds
    key = f"rate_limit:submissions:{user_id}"

    try:
        async with redis_client.pipeline() as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window_seconds)
            results = await pipe.execute()

        current_count = results[1]
        return current_count < max_requests

    except Exception:
        return True


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting.

    Usage:
        app.add_middleware(RateLimitMiddleware)
    """

    def __init__(self, app, redis_client=None):
        self.app = app
        self.redis_client = redis_client

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        if request.url.path.startswith("/api/assessment/") and request.method == "POST":
            user_id = request.headers.get("X-User-Id", request.client.host)
            allowed = await check_rate_limit(user_id, self.redis_client)

            if not allowed:
                response = HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Max 10 submissions per hour.",
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
