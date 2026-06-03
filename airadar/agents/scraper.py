"""Scraper agent (Architecture §4.2).

Consumes candidate_urls in state ``pending_scrape``, fetches+cleans each, and writes a
``raw_pages`` row. Advances the candidate's status to ``scraped`` (ready for enrichment),
``low_quality``, ``duplicate_html``, or ``failed``.

Responsibility boundary (R2): fetch and clean only. No extraction/LLM — that's R3.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.config import get_settings
from airadar.db.models import PipelineRun
from airadar.db.repositories import candidate_urls as candidate_repo
from airadar.db.repositories import raw_pages as raw_repo
from airadar.scraping.orchestrator import fetch


@dataclass
class ScrapeStageResult:
    scraped: int
    low_quality: int
    duplicate_html: int
    failed: int


async def run_scraper(session: AsyncSession, limit: int = 100) -> ScrapeStageResult:
    """Scrape all pending candidates (up to ``limit``)."""
    settings = get_settings()
    pending = await candidate_repo.get_by_status(session, "pending_scrape", limit=limit)

    run = PipelineRun(stage="scraper", status="running", items_in=len(pending))
    session.add(run)

    scraped = low_quality = duplicate_html = failed = 0
    for candidate in pending:
        candidate_repo.set_status(candidate, "scraping")
        result = await fetch(candidate.url, min_word_count=settings.min_word_count)

        # Content dedup: identical HTML already scraped → skip enrichment.
        if result.html_hash and await raw_repo.html_hash_seen(session, result.html_hash):
            await raw_repo.insert(
                session,
                candidate.id,
                clean_text=None,
                html_hash=result.html_hash,
                word_count=result.word_count,
                fetcher_used=result.fetcher_used,
                status="duplicate_html",
            )
            candidate_repo.set_status(candidate, "duplicate_html")
            duplicate_html += 1
            continue

        await raw_repo.insert(
            session,
            candidate.id,
            clean_text=result.clean_text,
            html_hash=result.html_hash,
            word_count=result.word_count,
            fetcher_used=result.fetcher_used,
            status=result.status,
        )

        if result.status == "ok":
            candidate_repo.set_status(candidate, "scraped")
            scraped += 1
        elif result.status == "low_quality":
            candidate_repo.set_status(candidate, "low_quality")
            low_quality += 1
        else:
            candidate_repo.set_status(candidate, "failed")
            failed += 1

    run.status = "ok"
    run.finished_at = datetime.now(UTC)
    run.items_out = scraped
    logger.info(
        "Scraper: scraped={} low_quality={} duplicate_html={} failed={}",
        scraped,
        low_quality,
        duplicate_html,
        failed,
    )
    return ScrapeStageResult(scraped, low_quality, duplicate_html, failed)
