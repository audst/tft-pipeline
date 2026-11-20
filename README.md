# TFT Pipeline

![CI](https://github.com/<you>/tft-pipeline/actions/workflows/ci.yml/badge.svg)

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

## Architecture

```
Riot API → async ingester → raw JSON (bronze) → Spark job → Parquet (silver)
        → DuckDB gold tables → LightGBM + AVP aggregates
                 orchestrated by Airflow, run in Docker, tested in GitHub Actions
```

- **Bronze:** raw match JSON, stored untouched
- **Silver:** flattened tables (`matches`, `participants`, `participant_traits`, `participant_units`, `participant_augments`), partitioned by patch
- **Gold:** model-ready features and aggregated AVP tables

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

- [x] Repo, uv, and CI setup
- [ ] Rate limiter and async Riot client
- [ ] Seed players and fetch match IDs
- [ ] Raw JSON storage (idempotent)
- [ ] Spark flattening to Parquet
- [ ] Airflow DAG and Docker Compose
- [ ] Gold tables and AVP analysis
- [ ] LightGBM placement model
- [ ] Final write-up and results

## Design notes and limitations

- **End-state features:** `level` and `gold_left` come from post-game snapshots, so the model describes final boards rather than forecasting from early game. Strong boards and survival time are correlated.
- **Pick rate matters:** a comp contested by several players in one lobby has a lower AVP than its uncontested potential, so AVP is reported alongside pick rate.
- **Patch drift:** data is never mixed across patches or sets.

## License

MIT