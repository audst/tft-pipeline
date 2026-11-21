import asyncio

from tft_pipeline.ratelimit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds
        await asyncio.sleep(0)  # yield so concurrent tasks really interleave


def make(limits):
    clock = FakeClock()
    return RateLimiter(limits, clock=clock, sleep=clock.sleep), clock