# TFT Pipeline

![CI](https://github.com/audst/tft-pipeline/actions/workflows/ci.yml/badge.svg)

A data pipeline for Teamfight Tactics (TFT) that ingests high-elo match data from the Riot API, transforms it into partitioned Parquet tables, and uses it to model placements and compute average placement (AVP) by composition and augment.

## Why!!!

I love playing TFT and I'm currently climbing set 18 (Diamond). The thing
that fascinates me about the game is that placement is decided less by
mechanics than by decisions under incomplete information: when to save versus
spend, how much health to trade for tempo, whether to commit to a comp or stay
flexible, and how to read what the lobby is contesting.

Riot's match data only exposes post-game snapshots, so it can't see most of
those decisions directly. This project asks what the final boards can tell
us: how much unspent gold at elimination signals poor tempo, how contested
comps affect average placement, and which augments and items actually move
results. The pipeline is the engineering half; the questions come from the
climb!

## What works as of today

- Seeds players from the Challenger, Grandmaster, and Master leagues, skipping inactive accounts
- Async Riot client with a custom rate limiter, jittered retries, and clear handling of expired keys
- Match ID collection with deduplication across players
- Idempotent, crash-safe raw storage: reruns skip matches already on disk
- Unit tests (fake clock, mocked HTTP) and CI on every push

## Architecture

```
Riot API → async client + rate limiter → raw JSON (bronze)
        → Spark flattening → Parquet (silver)   [planned]
        → gold tables + model                    [planned]
```

## Features

- Seeds Challenger, Grandmaster, and Master players from TFT-LEAGUE-V1
- Async fetcher with a custom token-bucket rate limiter (20 req/s, 100 req/2 min) and exponential backoff on 429/5xx
- Idempotent ingestion: reruns skip matches already downloaded
- Single-patch filtering so balance changes don't corrupt labels
- Data quality checks (8 participants per match, placements 1-8, no null keys)
- Match-grouped train/test split to prevent leakage between players in the same lobby

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and a Riot API key from the [Riot developer portal](https://developer.riotgames.com/). Dev keys expire every 24 hours.

```bash
git clone git@github.com:<you>/tft-pipeline.git
cd tft-pipeline
cp .env.example .env        # then add your RIOT_API_KEY
uv sync
uv run pytest
uv run python -m tft_pipeline.pipeline
```

## Project structure

```
src/tft_pipeline/   # config, rate limiter, Riot client, seeding, ingestion
spark_jobs/         # PySpark flattening jobs
dags/               # Airflow DAGs
sql/                # gold-layer aggregates
tests/              # pytest suite
docs/               # diagrams and design notes
```

## Status

- [x] Repo, uv, and CI
- [x] Rate limiter with tests
- [x] Async Riot client with retries and tests
- [x] Seeding and match ID collection
- [x] Idempotent raw storage
- [x] First end-to-end run against the live API
- [ ] Large download run
- [ ] Spark flattening to Parquet
- [ ] Data quality checks
- [ ] Orchestration and Docker
- [ ] Gold tables and AVP analysis
- [ ] Placement model

## Design notes and limitations

- **End-state features:** `level` and `gold_left` come from post-game snapshots, so the model describes final boards rather than forecasting from early game. Strong boards and survival time are correlated.
- **Pick rate matters:** a comp contested by several players in one lobby has a lower AVP than its uncontested potential, so AVP is reported alongside pick rate.
- **Patch drift:** data is never mixed across patches or sets.

## License

MIT