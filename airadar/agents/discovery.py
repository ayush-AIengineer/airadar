"""Discovery agent (Architecture §4.1).

Finds candidate URLs that *might* describe a newly launched AI tool, classifies them
cheaply, and persists those above the signal threshold as ``pending_scrape``.

Responsibility boundary (R1): adapters fetch, the classifier scores, this agent persists
and records the run. It does not scrape or enrich — that's R2/R3.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.agents.classifier import SignalClassifier
from airadar.config import get_settings
from airadar.db.models import PipelineRun
from airadar.db.repositories import candidate_urls as candidate_repo
from airadar.db.repositories import sources as source_repo
from airadar.sources.registry import get_adapter


@dataclass
class DiscoveryResult:
    source_slug: str
    fetched: int
    accepted: int
    rejected: int
    duplicates: int


async def run_discovery(
    session: AsyncSession,
    source_slug: str,
    lookback_hours: int = 24,
) -> DiscoveryResult:
    """Run the Discovery stage for a single source."""
    settings = get_settings()
    threshold = settings.discovery_signal_threshold

    source = await source_repo.get_by_slug(session, source_slug)
    if source is None:
        raise ValueError(
            f"Source {source_slug!r} not in registry. Run `airadar seed-sources` first."
        )

    run = PipelineRun(stage="discovery", source_id=source.id, status="running")
    session.add(run)

    adapter = get_adapter(source.adapter_class)
    classifier = SignalClassifier(use_llm=bool(settings.anthropic_api_key))
    since = datetime.now(UTC) - timedelta(hours=lookback_hours)

    fetched = accepted = rejected = duplicates = 0
    try:
        candidates = await adapter.fetch_since(since)
        fetched = len(candidates)
        for candidate in candidates:
            signal = await classifier.score(candidate)
            # <0.4 → dropped silently (logged only), per §4.1.
            if signal < 0.4:
                rejected += 1
                continue
            status = "pending_scrape" if signal >= threshold else "rejected"
            row = await candidate_repo.insert_new(
                session, source.id, candidate, signal, status
            )
            if row is None:
                duplicates += 1
            elif status == "pending_scrape":
                accepted += 1
            else:
                rejected += 1

        await source_repo.mark_run(session, source, "ok")
        run.status = "ok"
    except Exception as exc:
        run.status = "error"
        run.error_message = str(exc)
        await source_repo.mark_run(session, source, "error")
        logger.exception("Discovery failed for {}", source_slug)
        raise
    finally:
        run.finished_at = datetime.now(UTC)
        run.items_in = fetched
        run.items_out = accepted

    logger.info(
        "Discovery[{}]: fetched={} accepted={} rejected={} dup={}",
        source_slug,
        fetched,
        accepted,
        rejected,
        duplicates,
    )
    return DiscoveryResult(source_slug, fetched, accepted, rejected, duplicates)
