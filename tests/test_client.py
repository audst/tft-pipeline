
import httpx
import pytest

from tft_pipeline.client import RiotAuthError, RiotClient
from tft_pipeline.config import Config
from tft_pipeline.ratelimit import RateLimiter


def make_client(handler):
    async def no_sleep(_seconds):
        pass

    return RiotClient(
        Config(api_key="k"),
        RateLimiter([(1000, 1)]),
        transport=httpx.MockTransport(handler),
        sleep=no_sleep,
    )

async def test_success_returns_entries():
    def handler(request):
        return httpx.Response(200, json={"entries": [{"puuid": "a"}]})

    async with make_client(handler) as client:
        result = await client.league_entries("challenger")

    assert result == [{"puuid": "a"}]


async def test_retries_429_then_succeeds():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"entries": [{"puuid": "a"}]})

    async with make_client(handler) as client:
        assert await client.league_entries("challenger") == [{"puuid": "a"}]
    assert len(calls) == 2


async def test_auth_error_is_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(401)

    async with make_client(handler) as client:
        with pytest.raises(RiotAuthError):
            await client.league_entries("challenger")
    assert len(calls) == 1


async def test_404_returns_none():
    async with make_client(lambda r: httpx.Response(404)) as client:
        assert await client.match("NA1_1") is None