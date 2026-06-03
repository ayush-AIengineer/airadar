"""Repository for scraped pages."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.db.models import RawPage


async def html_hash_seen(session: AsyncSession, html_hash: str) -> bool:
    """True if a prior page already has this HTML hash (content dedup, §4.2)."""
    existing = await session.scalar(
        select(RawPage.id).where(RawPage.html_hash == html_hash)
    )
    return existing is not None


async def insert(
    session: AsyncSession,
    candidate_url_id: uuid.UUID,
    *,
    clean_text: str | None,
    html_hash: str | None,
    word_count: int,
    fetcher_used: str | None,
    status: str,
) -> RawPage:
    row = RawPage(
        candidate_url_id=candidate_url_id,
        clean_text=clean_text,
        html_hash=html_hash,
        word_count=word_count,
        fetcher_used=fetcher_used,
        status=status,
    )
    session.add(row)
    return row


async def get_for_candidate(
    session: AsyncSession, candidate_url_id: uuid.UUID
) -> RawPage | None:
    result: RawPage | None = await session.scalar(
        select(RawPage).where(RawPage.candidate_url_id == candidate_url_id)
    )
    return result
