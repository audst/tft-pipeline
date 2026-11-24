import asyncio
import logging
import random

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

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(30.0, 2.0**attempt) * random.uniform(0.5, 1.0)  # jittered

    async def _get(self, url, params=None):
        for attempt in range(self._max_retries):
            await self._limiter.acquire()  # every retry goes back through the limiter
            try:
                async with self._sem:
                    resp = await self._http.get(url, params=params)
            except httpx.TransportError as exc:
                log.warning("network error on %s (attempt %d): %s", url, attempt + 1, exc)
                await self._sleep(self._backoff(attempt))
                continue

            status = resp.status_code
            if status == 200:
                return resp.json()
            if status == 404:
                return None
            if status in (401, 403):
                raise RiotAuthError(f"{status} from Riot. Dev keys expire every 24h; regenerate yours.")
            if status == 429:
                delay = float(resp.headers.get("Retry-After", self._backoff(attempt)))
            elif status >= 500:
                delay = self._backoff(attempt)
            else:
                resp.raise_for_status()  # other 4xx means a bug in our request
            log.warning("status %d on %s (attempt %d), waiting %.1fs", status, url, attempt + 1, delay)
            await self._sleep(delay)
        raise RuntimeError(f"gave up on {url} after {self._max_retries} attempts")

    async def league_entries(self, tier: str) -> list[dict]:
        data = await self._get(f"{self._cfg.platform_url}/tft/league/v1/{tier}")
        return data["entries"] if data else []

    async def match_ids(self, puuid: str, count: int = 20, start_time: int | None = None) -> list[str]:
        params = {"count": count}
        if start_time:
            params["startTime"] = start_time
        url = f"{self._cfg.region_url}/tft/match/v1/matches/by-puuid/{puuid}/ids"
        return await self._get(url, params) or []

    async def match(self, match_id: str) -> dict | None:
        return await self._get(f"{self._cfg.region_url}/tft/match/v1/matches/{match_id}")