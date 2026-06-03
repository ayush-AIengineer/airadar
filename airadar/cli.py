"""AIRadar command-line runner (R9).

Phase 1 entrypoint. `pipeline-once` currently runs the Discovery stage; Scraper and
Enrichment stages chain in here as they land, producing the Phase 1 deliverable:
enriched tool records in the DB from a single manual run.
"""

from __future__ import annotations

import asyncio

import typer
from loguru import logger

from airadar.agents.discovery import run_discovery
from airadar.agents.enrichment import run_enrichment
from airadar.agents.scraper import run_scraper
from airadar.db.repositories import sources as source_repo
from airadar.db.session import session_scope
from airadar.sources.registry import get_adapter

app = typer.Typer(add_completion=False, help="AIRadar pipeline CLI.")


@app.command("seed-sources")
def seed_sources_cmd() -> None:
    """Load the source registry into the database."""

    async def _run() -> int:
        async with session_scope() as session:
            return await source_repo.seed_sources(session)

    inserted = asyncio.run(_run())
    typer.echo(f"Seeded {inserted} new source(s).")


@app.command("health")
def health_cmd(source: str = typer.Option(..., help="Source slug, e.g. hackernews")) -> None:
    """Check whether a source is reachable."""

    async def _run() -> None:
        async with session_scope() as session:
            row = await source_repo.get_by_slug(session, source)
            if row is None:
                typer.echo(f"Unknown source {source!r}. Run seed-sources first.")
                raise typer.Exit(code=1)
            adapter = get_adapter(row.adapter_class)
            health = await adapter.health_check()
        status = "OK" if health.ok else "FAIL"
        typer.echo(f"[{status}] {source}: {health.detail}")

    asyncio.run(_run())


@app.command("pipeline-once")
def pipeline_once_cmd(
    source: str = typer.Option(..., help="Source slug, e.g. hackernews"),
    lookback_hours: int = typer.Option(24, help="How far back to fetch."),
    limit: int = typer.Option(25, help="Max candidates to scrape+enrich this run."),
) -> None:
    """Run the full pipeline once for a source: discovery → scrape → enrich.

    Each stage commits in its own transaction so a later failure preserves earlier work.
    """

    async def _discover() -> None:
        async with session_scope() as session:
            r = await run_discovery(session, source, lookback_hours=lookback_hours)
        typer.echo(
            f"  discovery: fetched={r.fetched} accepted={r.accepted} "
            f"rejected={r.rejected} duplicates={r.duplicates}"
        )

    async def _scrape() -> None:
        async with session_scope() as session:
            r = await run_scraper(session, limit=limit)
        typer.echo(
            f"  scraper:   scraped={r.scraped} low_quality={r.low_quality} "
            f"duplicate_html={r.duplicate_html} failed={r.failed}"
        )

    async def _enrich() -> None:
        async with session_scope() as session:
            r = await run_enrichment(session, limit=limit)
        typer.echo(
            f"  enrich:    enriched={r.enriched} duplicates={r.duplicates} "
            f"skipped={r.skipped} fields_blanked={r.fields_blanked}"
        )

    logger.info("pipeline-once starting for source={}", source)
    typer.echo(f"pipeline-once [{source}]:")
    asyncio.run(_discover())
    asyncio.run(_scrape())
    asyncio.run(_enrich())


if __name__ == "__main__":
    app()
