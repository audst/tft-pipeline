import asyncio
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

async def collect_match_ids(client, puuids, per_player, start_time) -> set[str]:
    results = await asyncio.gather(
        *(client.match_ids(p, count=per_player, start_time=start_time) for p in puuids)
    )
    total = sum(len(r) for r in results)
    unique = {match_id for r in results for match_id in r}
    log.info(
        "collected %d ids, %d unique (%d duplicates removed)",
        total, len(unique), total - len(unique),
    )
    return unique

async def fetch_one(client, match_id: str, root: Path) -> str:
    path = root / f"{match_id}.json"
    if path.exists():
        return "skipped"

    match = await client.match(match_id)
    if match is None:
        return "missing"

    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(match))
    tmp.replace(path)
    return "fetched"