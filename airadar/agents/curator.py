"""Curator / Dedup agent (Architecture §4.4).

Decides what's worth publishing: collapses duplicates (conservatively, never deleting)
and assigns a transparent quality score. Runs after enrichment.

Dedup ladder — first trigger wins (R4):
  1. Domain match     — same registered domain as a recent kept tool
  2. Semantic match   — cosine ≥ threshold vs Qdrant, within lookback window
  3. Name-fuzzy match — Levenshtein ≤ 2 on normalized names

Exact canonical-URL duplicates are already prevented at enrichment insert
(``tools.canonical_url_hash`` unique), so the ladder starts at domain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import tldextract
from loguru import logger
from rapidfuzz.distance import Levenshtein
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.config import get_settings
from airadar.db.models import PipelineRun, Tool
from airadar.db.repositories import tools as tools_repo
from airadar.dedup.embeddings import get_embedder
from airadar.dedup.qdrant_client import DedupIndex
from airadar.dedup.scorer import ToolSignals, quality_score


@dataclass
class CurateResult:
    curated: int
    duplicates: int
    published: int  # non-dup with quality_score >= 30


# Multi-tenant hosts: many unrelated tools live under one registered domain, so a
# domain match here is a FALSE positive. Skip domain-match for these (semantic +
# name-fuzzy still apply). Conservative dedup is the whole point (R4).
_MULTI_TENANT_DOMAINS = frozenset(
    {
        "github.com",
        "gitlab.com",
        "news.ycombinator.com",
        "ycombinator.com",
        "huggingface.co",
        "medium.com",
        "dev.to",
        "substack.com",
        "notion.site",
        "reddit.com",
        "producthunt.com",
        "youtube.com",
        "twitter.com",
        "x.com",
        "vercel.app",
        "netlify.app",
        "herokuapp.com",
        "streamlit.app",
        "replit.app",
    }
)


def _registered_domain(url: str) -> str:
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}".lower().strip(".")


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _embed_text(tool: Tool) -> str:
    cats = " ".join(c.slug for c in tool.categories)
    return f"{tool.name} {tool.one_liner or ''} {cats}".strip()


async def run_curator(session: AsyncSession, limit: int = 200) -> CurateResult:
    settings = get_settings()
    embedder = get_embedder(settings.openai_api_key)
    index = DedupIndex(settings.qdrant_path, dim=embedder.dim)
    await index.ensure_collection()

    since = datetime.now(UTC) - timedelta(days=settings.dedup_lookback_days)
    recent = await tools_repo.list_curated_canonicals(session, since)
    domain_map = {_registered_domain(t.canonical_url): t.id for t in recent}
    name_map = [(_normalize_name(t.name), t.id) for t in recent]

    pending = await tools_repo.get_uncurated(session, limit=limit)
    run = PipelineRun(stage="curator", status="running", items_in=len(pending))
    session.add(run)

    curated = duplicates = published = 0
    try:
        for tool in pending:
            now = datetime.now(UTC)
            dup_of = None
            reason = ""

            # 1. Domain match (skip multi-tenant hosts to avoid false positives)
            domain = _registered_domain(tool.canonical_url)
            if domain not in _MULTI_TENANT_DOMAINS and domain in domain_map:
                dup_of, reason = domain_map[domain], f"domain match ({domain})"

            # 2. Semantic match
            vector = await embedder.embed(_embed_text(tool))
            if dup_of is None:
                hit = await index.nearest(vector, settings.dedup_lookback_days)
                if hit and hit[1] >= settings.dedup_similarity_threshold:
                    dup_of, reason = hit[0], f"semantic match (cos={hit[1]:.3f})"

            # 3. Name-fuzzy match
            if dup_of is None:
                norm = _normalize_name(tool.name)
                for other_norm, other_id in name_map:
                    if norm and Levenshtein.distance(norm, other_norm) <= 2:
                        dup_of, reason = other_id, f"name-fuzzy match ('{other_norm}')"
                        break

            if dup_of is not None:
                tool.is_duplicate_of_id = dup_of
                tool.decision_reason = reason
                tool.curated_at = now
                duplicates += 1
                curated += 1
                continue

            # Keep it: score, index, and register for in-batch matching.
            signals = ToolSignals(
                has_clear_pricing=bool(tool.pricing_model and tool.pricing_model != "unknown"),
                has_country=bool(tool.country_hq),
                description_length=len(tool.description or ""),
            )
            score = quality_score(signals)
            tool.quality_score = score
            tool.decision_reason = f"published (quality={score})"
            tool.curated_at = now
            await index.upsert(tool.id, vector, tool.name, tool.first_seen_at)
            domain_map[domain] = tool.id
            name_map.append((_normalize_name(tool.name), tool.id))
            curated += 1
            if score >= 30:
                published += 1

        run.status = "ok"
    except Exception as exc:
        run.status = "error"
        run.error_message = str(exc)
        logger.exception("Curator failed")
        raise
    finally:
        run.finished_at = datetime.now(UTC)
        run.items_out = published
        await index.close()

    logger.info(
        "Curator: curated={} duplicates={} published(score>=30)={}",
        curated,
        duplicates,
        published,
    )
    return CurateResult(curated, duplicates, published)
