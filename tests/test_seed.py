from tft_pipeline.seed import seed_puuids


class FakeClient:
    def __init__(self, data):
        self.data = data

    async def league_entries(self, tier):
        return self.data[tier]


def make(data):
    return FakeClient(data)


DATA = {
    "challenger": [{"puuid": "a"}, {"puuid": "b"}],
    "grandmaster": [{"puuid": "b"}, {"puuid": "c"}],
    "master": [{"puuid": "d"}],
}


async def test_duplicates_are_removed():
    result = await seed_puuids(make(DATA), cap=100)
    assert sorted(result) == ["a", "b", "c", "d"]


async def test_cap_limits_the_count():
    result = await seed_puuids(make(DATA), cap=2)
    assert len(result) == 2


async def test_same_seed_gives_same_sample():
    first = await seed_puuids(make(DATA), cap=2, rng_seed=1)
    second = await seed_puuids(make(DATA), cap=2, rng_seed=1)
    assert first == second