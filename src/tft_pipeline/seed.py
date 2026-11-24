import random

TIERS = ("challenger", "grandmaster", "master")


async def seed_puuids(client, cap: int, rng_seed: int = 42) -> list[str]:
    puuids = set()
    for tier in TIERS:
        for entry in await client.league_entries(tier):
            puuids.add(entry["puuid"])

    ordered = sorted(puuids)
    random.Random(rng_seed).shuffle(ordered)
    return ordered[:cap]