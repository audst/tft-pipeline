import asyncio
import collections
import logging
from pathlib import Path
import time

from .client import RiotClient
from .config import Config
from .ingest import collect_match_ids, fetch_one
from .ratelimit import RateLimiter
from .seed import seed_puuids

log = logging.getLogger(__name__)

async def run(players: int, per_player: int, max_matches: int, days: int, rng_seed: int = 42):
    # load config
    cfg = Config.from_env()
    
    # create data folder
    root = Path("data/raw") / cfg.platform
    root.mkdir(parents=True, exist_ok=True)

    # build rate limiter
    limiter = RateLimiter([(100, 120), (20, 1)])
    
    async with RiotClient(cfg, limiter) as client:
        puuids = await seed_puuids(client, cap=players, rng_seed=rng_seed)

        start_time = int(time.time()) - days * 86400
        match_ids = await collect_match_ids(client, puuids, per_player, start_time)

        have = {p.stem for p in root.glob("*.json")}
        todo = sorted(match_ids - have)[:max_matches]
        log.info("%d new matches to fetch (%d already on disk)", len(todo), len(match_ids & have))

        results = await asyncio.gather(*(fetch_one(client, m, root) for m in todo))
        log.info("done: %s", dict(collections.Counter(results)))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run(players=20, per_player=5, max_matches=20, days=7))