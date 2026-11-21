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

async def test_no_wait_within_limit():
    rl, clock = make([(3, 10)])
    for _ in range(3):
        await rl.acquire()
    assert clock.sleeps == []


async def test_extra_request_waits_for_oldest_to_expire():
    rl, clock = make([(3, 10)])
    for _ in range(4):
        await rl.acquire()
    assert clock.sleeps == [10]


async def test_capacity_returns_after_window():
    rl, clock = make([(3, 10)])
    for _ in range(3):
        await rl.acquire()
    clock.now += 10
    await rl.acquire()
    assert clock.sleeps == []


async def test_stricter_limit_wins():
    rl, clock = make([(100, 120), (20, 1)])
    for _ in range(21):
        await rl.acquire()
    assert clock.sleeps == [1]


async def test_no_double_window_burst():
    rl, clock = make([(100, 120)])
    for _ in range(101):
        await rl.acquire()
    assert clock.sleeps == [120]


async def test_concurrent_acquires_respect_limit():
    rl, clock = make([(3, 10)])
    times = []

    async def worker():
        await rl.acquire()
        times.append(clock.now)

    await asyncio.gather(*(worker() for _ in range(10)))
    assert sorted(times) == [0, 0, 0, 10, 10, 10, 20, 20, 20, 30]