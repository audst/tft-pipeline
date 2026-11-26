import asyncio
import logging

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