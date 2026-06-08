# AIRadar

Multi-agent system that discovers, enriches, deduplicates, and delivers daily
intelligence about newly launched AI tools.

- **What & why:** [AIRadar-Architecture.md](AIRadar-Architecture.md) — the single source of truth.
- **Who builds what:** [AIRadar-Agent-Roles.md](AIRadar-Agent-Roles.md) — pick a role before you touch a stage.

## Status

**Phase 1 — Foundations** (walking skeleton). Local datastore is **SQLite** (no Docker
needed yet); models stay Postgres-compatible and swap over in Phase 2.

## Quick start

Requires [`uv`](https://docs.astral.sh/uv/). On Windows, run the `uv` commands directly
if `make` is unavailable.

```bash
uv python pin 3.12          # match the architecture's target runtime
uv sync --all-groups        # or: make install
cp .env.example .env        # SQLite default works out of the box

uv run alembic upgrade head # create the schema   (make migrate)
uv run airadar seed-sources # load the source registry   (make seed)
uv run airadar pipeline-once --source hackernews   # (make pipeline-once SOURCE=hackernews)

# Delivery stage (Stage 5): add a subscriber, then build + send their digest.
# With no AIRADAR_RESEND_API_KEY set, rendered digests are written to ./outbox/.
uv run airadar add-user --email you@example.com --min-score 0
uv run airadar deliver                # send once, now, to all subscribers

# Or run the scheduler: it wakes every 15 min and delivers each user's digest at
# their own digest_cron time (in their timezone), idempotently — one per local day.
uv run airadar run-scheduler
```

## Layout

See [Architecture §9](AIRadar-Architecture.md) for the full tree. The five pipeline
stages live in `airadar/agents/` (discovery → scraper → enrichment → curator → delivery),
with source adapters in `airadar/sources/` and the data layer in `airadar/db/`.

## Dev

```bash
make test        # uv run pytest        (VCR cassettes, no live network)
make lint        # uv run ruff check .
make typecheck   # uv run mypy airadar
```
