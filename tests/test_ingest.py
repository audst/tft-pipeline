from tft_pipeline.ingest import collect_match_ids


class FakeClient:
    def __init__(self, data):
        self.data = data
        self.calls = []

    async def match_ids(self, puuid, count=20, start_time=None):
        self.calls.append((puuid, count, start_time))
        return self.data[puuid]


DATA = {
    "p1": ["m1", "m2", "m3"],
    "p2": ["m2", "m3", "m4"],  # shares m2 and m3 with p1
    "p3": [],                  # a player with no recent games
}


async def test_duplicates_are_removed():
    client = FakeClient(DATA)
    result = await collect_match_ids(client, ["p1", "p2", "p3"], per_player=20, start_time=0)
    assert result == {"m1", "m2", "m3", "m4"}


async def test_every_player_is_queried_with_the_given_settings():
    client = FakeClient(DATA)
    await collect_match_ids(client, ["p1", "p2"], per_player=5, start_time=123)
    assert sorted(client.calls) == [("p1", 5, 123), ("p2", 5, 123)]


async def test_no_players_gives_empty_set():
    client = FakeClient({})
    assert await collect_match_ids(client, [], per_player=20, start_time=0) == set()