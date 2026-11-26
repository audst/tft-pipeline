import json

from tft_pipeline.ingest import fetch_one


class FakeClient:
    def __init__(self, matches):
        self.matches = matches
        self.calls = []

    async def match(self, match_id):
        self.calls.append(match_id)
        return self.matches.get(match_id)


async def test_new_match_is_saved(tmp_path):
    client = FakeClient({"m1": {"info": {"x": 1}}})

    result = await fetch_one(client, "m1", tmp_path)

    assert result == "fetched"
    assert json.loads((tmp_path / "m1.json").read_text()) == {"info": {"x": 1}}
    assert not (tmp_path / "m1.tmp").exists()


async def test_existing_match_is_skipped_without_a_request(tmp_path):
    (tmp_path / "m1.json").write_text("{}")
    client = FakeClient({"m1": {"info": {}}})

    result = await fetch_one(client, "m1", tmp_path)

    assert result == "skipped"
    assert client.calls == []


async def test_missing_match_writes_nothing(tmp_path):
    client = FakeClient({})

    result = await fetch_one(client, "m1", tmp_path)

    assert result == "missing"
    assert list(tmp_path.iterdir()) == []