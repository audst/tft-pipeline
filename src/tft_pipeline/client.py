import asyncio
import logging

import httpx

from .config import Config
from .ratelimit import RateLimiter

log = logging.getLogger(__name__)


class RiotAuthError(RuntimeError):
    """401/403: bad or expired key. Retrying can't help."""


class RiotClient:
    def __init__(self, cfg: Config, limiter: RateLimiter, *, max_retries=5,
                 concurrency=10, transport=None, sleep=asyncio.sleep):
        self._cfg = cfg
        self._limiter = limiter
        self._max_retries = max_retries
        self._sem = asyncio.Semaphore(concurrency)
        self._sleep = sleep
        self._http = httpx.AsyncClient(
            headers={"X-Riot-Token": cfg.api_key}, timeout=15.0, transport=transport
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._http.aclose()
