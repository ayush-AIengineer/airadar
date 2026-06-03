"""Enrichment agent (Architecture §4.3) — the most quality-critical stage.

Consumes ``scraped`` candidates, extracts a structured :class:`ToolEnrichment`, verifies
each evidence-bearing field against the source text (blanking unsupported fields), then
writes a canonical ``tools`` row + ``tool_evidence`` rows. Advances the candidate to
``enriched``.

Cost discipline (R13): respects the daily enrichment cap; the cheap verifier never uses
Sonnet. Hallucination guard (R3): no field survives without grounded evidence.
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
from airadar.db.repositories import tools as tools_repo
from airadar.llm.client import get_extractor
from airadar.llm.schema import PricingModel, ToolEnrichment
from airadar.llm.verifiers import quote_is_grounded


@dataclass
class EnrichStageResult:
    enriched: int
    duplicates: int
    skipped: int
    fields_blanked: int


def _verify_and_blank(enr: ToolEnrichment, source_text: str) -> int:
    """Blank fields whose evidence quote is not grounded in the source. Returns count."""
    blanked = 0
    if enr.pricing_model is not PricingModel.unknown and not quote_is_grounded(
        enr.pricing_evidence_quote, source_text
    ):
        enr.pricing_model = PricingModel.unknown
        enr.pricing_evidence_quote = None
        enr.starting_price_usd_monthly = None
        blanked += 1
    if enr.country_hq and not quote_is_grounded(enr.country_evidence, source_text):
        enr.country_hq = None
        enr.country_evidence = None
        blanked += 1
    if enr.launch_date_iso and not quote_is_grounded(enr.launch_date_evidence, source_text):
        enr.launch_date_iso = None
        enr.launch_date_evidence = None
        blanked += 1
    return blanked


async def run_enrichment(session: AsyncSession, limit: int | None = None) -> EnrichStageResult:
    settings = get_settings()
    cap = limit if limit is not None else settings.max_enrichment_per_day
    extractor = get_extractor(settings)

    pending = await candidate_repo.get_by_status(session, "scraped", limit=cap)
    run = PipelineRun(stage="enrichment", status="running", items_in=len(pending))
    session.add(run)

    enriched = duplicates = skipped = fields_blanked = 0
    for candidate in pending:
        page = await raw_repo.get_for_candidate(session, candidate.id)
        if page is None or not page.clean_text:
            candidate_repo.set_status(candidate, "failed")
            skipped += 1
            continue

        enr = await extractor.extract(
            title=candidate.raw_title or "",
            url=candidate.url,
            text=page.clean_text,
        )
        fields_blanked += _verify_and_blank(enr, page.clean_text)

        if await tools_repo.exists_by_hash(
            session, tools_repo.canonical_hash(enr.canonical_url)
        ):
            candidate_repo.set_status(candidate, "enriched")
            duplicates += 1
            continue

        tool = await tools_repo.insert_tool(
            session,
            name=enr.name,
            canonical_url=enr.canonical_url,
            one_liner=enr.one_liner,
            description=enr.description,
            pricing_model=enr.pricing_model.value,
            starting_price_usd_monthly=enr.starting_price_usd_monthly,
            country_hq=enr.country_hq,
            launch_date=enr.launch_date_iso,
            is_open_source=enr.is_open_source,
            github_url=enr.github_url,
            confidence_score=enr.confidence_score,
            category_slugs=[c.value for c in enr.categories],
        )

        now = datetime.now(UTC)
        if enr.pricing_model is not PricingModel.unknown and enr.pricing_evidence_quote:
            tools_repo.add_evidence(
                session,
                tool_id=tool.id,
                field_name="pricing_model",
                field_value=enr.pricing_model.value,
                evidence_quote=enr.pricing_evidence_quote,
                evidence_url=enr.canonical_url,
                extracted_at=now,
            )
        if enr.country_hq and enr.country_evidence:
            tools_repo.add_evidence(
                session,
                tool_id=tool.id,
                field_name="country_hq",
                field_value=enr.country_hq,
                evidence_quote=enr.country_evidence,
                evidence_url=enr.canonical_url,
                extracted_at=now,
            )

        candidate_repo.set_status(candidate, "enriched")
        enriched += 1

    run.status = "ok"
    run.finished_at = datetime.now(UTC)
    run.items_out = enriched
    logger.info(
        "Enrichment: enriched={} duplicates={} skipped={} fields_blanked={}",
        enriched,
        duplicates,
        skipped,
        fields_blanked,
    )
    return EnrichStageResult(enriched, duplicates, skipped, fields_blanked)
