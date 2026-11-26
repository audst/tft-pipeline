# Riot TFT API notes

Observed by running `scripts/explore.py` against the live API. Dates are included because Riot changes things.

## Routing

| Purpose | Host type | Example host |
|---|---|---|
| League endpoints (seeding) | Platform | `na1.api.riotgames.com` |
| Match endpoints | Regional | `<fill in once you test>` |

Auth: key sent in the `X-Riot-Token` header.

## League endpoints (tested <date>)

- Challenger response is a dict with keys: `tier` (str), `queue` (str), `entries` (list), plus `<others you saw>`
- 250 entries at time of testing
- Each entry has 9 fields: "puuid",
  "leaguePoints",
  "rank",
  "wins",
  "losses",
  "veteran",
  "inactive",
  "freshBlood",
  "hotStreak"
- **Entries include `puuid` directly**, so no ID conversion is needed
- Grandmaster / Master: same shape as Challenger, more entries

## Rate limits

Headers observed on a league call:

```
x-app-rate-limit: 100:120,20:1
x-app-rate-limit-count: 1:120,1:1
x-method-rate-limit: 500:600,30:10
x-method-rate-limit-count: 7:600,1:10
```

Format is `max:window_seconds`, comma-separated. Order is not guaranteed, so parse the window from the number after the colon.

- App limits: 100 per 120 s and 20 per 1 s (across all endpoints on this host)
- Method limits: 500 per 600 s and 30 per 10 s (this endpoint only)
- Method limits can be stricter than app limits in the short window (30 per 10 s is 3/s vs. 20/s)

## Design implications

- The limiter must accept a list of `(max, window)` pairs and require a token from every one, not a hardcoded two
- Sustained throughput is about 50 requests/minute, so concurrency can't beat the limit, only keep me close to it
- Estimated time: 250 players is about 5 min of match-ID calls; 10k matches is about 3+ hours
- Possible future improvement: read the count headers after each response and adapt

## Raw Storage
- Files are stored as raw/{platform}/{match_id}.json, not by patch, because the patch is only known after downloading the match
- Writes are atomic (temp file, then rename)
- Restarting skips existing files, so that no requests are wasted

## Errors

| Status | Cause | Behavior |
|---|---|---|
| 200 | OK | parse JSON |
| 401/403 | unauthorized/forbidden | fail fast, no retry |
| 404 | `<test with a wrong URL>` | |
| 429 | `<untested yet>` | |
