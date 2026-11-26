# Riot TFT API notes

Observed by running the pipeline against the live API. Dates are included because Riot changes things.
Last updated: <date>

## Routing

| Purpose | Host type | Host |
|---|---|---|
| League endpoints (seeding) | Platform | `na1.api.riotgames.com` |
| Match endpoints | Regional | `americas.api.riotgames.com` |

- Auth: key sent in the `X-Riot-Token` header, not in the URL.
- Dev keys expire every 24 hours.

## League endpoints (tested <date>)

- Challenger, Grandmaster, and Master share one URL pattern; only the tier name changes, so `seed.py` uses one function in a loop.
- Response is a dict with keys `tier` (str), `queue` (str), `entries` (list), plus `<other keys you saw>`.
- Challenger had 250 entries at time of testing. Grandmaster and Master were larger: `<counts>`.
- Each entry has 9 fields: `puuid`, `leaguePoints`, `rank`, `wins`, `losses`, `veteran`, `inactive`, `freshBlood`, `hotStreak`.
- Entries include `puuid` directly, so no ID conversion step (saves one request per player).
- Seeding filters out `inactive` players, who likely have no recent matches and would waste requests.

## Rate limits

Headers observed on a league call:

```
x-app-rate-limit: 100:120,20:1
x-app-rate-limit-count: 1:120,1:1
x-method-rate-limit: 500:600,30:10
x-method-rate-limit-count: 7:600,1:10
```

- Format is `max:window_seconds`, comma-separated. Order is not guaranteed, so parse the window from the number after the colon.
- App limits: 100 per 120 s and 20 per 1 s (all endpoints on a host).
- Method limits: 500 per 600 s and 30 per 10 s (this endpoint only).
- The counts differ between windows because each window forgets old requests on its own schedule. My earlier runs had aged out of the 120 s window but were still inside the 600 s window.
- Match endpoint method limits: `<paste headers from a match response; not checked yet>`

## Match endpoints (tested <date>)

- Match IDs: returns a plain list of strings. `count` and `startTime` parameters work as expected: `<confirm>`.
- A match file has top-level keys: `<probably metadata and info; verify with jq 'keys'>`.
- `info.game_version` looks like: `<paste the exact string>`. The patch is parsed from this later.
- `queue_id` values seen: `<list them>`. Mixed queues will need filtering in Spark.
- A match ID can return 404: `<seen / not seen yet>`.

## First end-to-end run (<date>)

| Setting | Value |
|---|---|
| Players seeded | 20 |
| IDs requested per player | 5 |
| Window | last 7 days |
| IDs collected / unique / duplicates | `<n>` / `<n>` / `<n>` |
| Matches fetched | 18 |
| Skipped / missing | `<n>` / `<n>` |
| Time taken | `<seconds>` |

- Second run: `<did everything show as skipped? yes/no>`.

## Design decisions

**Sliding window over token bucket.** A token bucket enforces the average rate but permits a full-capacity burst on top of it. A 100-capacity bucket refilling over 120 s could let about 199 requests through in one 120 s window, while the server allows 100. The server counts a rolling window, so the limiter does too.

**A list of limits, not two.** Headers show four concurrent limits, so the limiter takes any number of `(max, window)` pairs and requires all of them to allow a request.

**Lock held while sleeping.** Waiters are released in order. This is correct because the limit is global.

**Injectable clock and sleep.** Tests advance a fake clock instead of really waiting.

**Errors are classified by what should happen next.** 429 and 5xx are retried with jittered backoff (honoring `Retry-After`), network errors are retried, 401/403 fail fast with a hint about key expiry, and 404 returns `None`.

**Raw files are stored by match ID, not patch.** Path is `data/raw/{platform}/{match_id}.json`. The patch is only known after downloading a match, so a patch-based path couldn't answer "do I already have this?" Patch filtering happens in the Spark step instead.

**Atomic writes.** Each match is written to a `.tmp` file and then renamed, so a crash never leaves a half-written `.json` that the skip check would trust.

**Idempotent runs.** Existing files are skipped without a request, so a restart wastes nothing.

**Reproducible seeding.** PUUIDs are sorted, then shuffled with a fixed random seed before the cap is applied.

## Budget estimates

- Sustained rate is about 50 requests/minute (100 per 120 s).
- Match IDs: 300 players is about 6 minutes; 1,000 players is about 20 minutes.
- Match downloads: 3,000 matches is about 1 hour; 10,000 is about 3.3 hours.
- Concurrency can't beat the rate limit; it only keeps the client close to it.

## Possible refinements

- Read the `x-*-rate-limit-count` headers and adapt, instead of only estimating.
- Use `gather(return_exceptions=True)` so one failed player doesn't stop ID collection.
- Use `wins`, `losses`, or `leaguePoints` to choose which players to sample.

## Open questions

- Match endpoint method limits on the regional host.
- Do the platform and regional hosts count limits separately?
- Which `queue_id` is ranked, and what share of matches does it make up?