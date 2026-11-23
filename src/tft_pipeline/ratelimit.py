import asyncio
import time
from collections import deque


class SlidingWindowLimit:
    """Allows at most `max_requests` in any rolling `window` seconds."""

    def __init__(self, max_requests: int, window: float):
        self.max_requests = max_requests
        self.window = window
        self._stamps: deque[float] = deque()

    def _expire(self, now: float) -> None:
        while self._stamps and now - self._stamps[0] >= self.window:
            self._stamps.popleft()

    def wait_time(self, now: float) -> float:
        self._expire(now)
        if len(self._stamps) < self.max_requests:
            return 0.0
        return self._stamps[0] + self.window - now

    def record(self, now: float) -> None:
        self._stamps.append(now)

class RateLimiter:
    def __init__(self, limits, clock=time.monotonic, sleep=asyncio.sleep):
        self._limits = [SlidingWindowLimit(m, w) for m, w in limits]
        self._clock = clock
        self._sleep = sleep
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = self._clock()
                wait = max(limit.wait_time(now) for limit in self._limits)
                if wait <= 0:
                    for limit in self._limits:
                        limit.record(now)
                    return
                await self._sleep(wait)