"""Repository for the source registry (one aggregate per file — R6 standard)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.db.models import Source

# The seed set (Architecture §5.1, Tier A). Product Hunt lands next (needs an API token).
SEED_SOURCES: list[dict[str, object]] = [
    {
        "slug": "hackernews",
        "name": "Hacker News",
        "adapter_class": "HackerNewsAdapter",
        "tier": "A",
        "rate_limit_rpm": 60,
    },
    {
        "slug": "github",
        "name": "GitHub",
        "adapter_class": "GitHubAdapter",
        "tier": "A",
        "rate_limit_rpm": 10,
    },
]


async def seed_sources(session: AsyncSession) -> int:
    """Insert seed sources that don't already exist. Returns the number inserted."""
    inserted = 0
    for spec in SEED_SOURCES:
        existing = await session.scalar(
            select(Source).where(Source.slug == spec["slug"])
        )
        if existing is None:
            session.add(Source(**spec))
            inserted += 1
    return inserted


async def get_by_slug(session: AsyncSession, slug: str) -> Source | None:
    result: Source | None = await session.scalar(
        select(Source).where(Source.slug == slug)
    )
    return result


async def list_enabled(session: AsyncSession) -> list[Source]:
    result = await session.scalars(select(Source).where(Source.enabled.is_(True)))
    return list(result)


async def mark_run(session: AsyncSession, source: Source, status: str) -> None:
    source.last_run_at = datetime.now(UTC)
    source.last_status = status
