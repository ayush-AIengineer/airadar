"""Repository for candidate URLs (discovery output)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.db.models import CandidateURL as CandidateURLRow
from airadar.sources.base import CandidateURL


async def insert_new(
    session: AsyncSession,
    source_id: uuid.UUID,
    candidate: CandidateURL,
    signal_score: float,
    status: str,
) -> CandidateURLRow | None:
    """Insert a candidate if its url_hash is unseen. Returns the row, or None if a dup.

    Dedup is by SHA256(url) via the unique ``url_hash`` constraint (Architecture §7.1).
    """
    url_hash = candidate.url_hash
    existing = await session.scalar(
        select(CandidateURLRow.id).where(CandidateURLRow.url_hash == url_hash)
    )
    if existing is not None:
        return None

    row = CandidateURLRow(
        source_id=source_id,
        url=candidate.url,
        url_hash=url_hash,
        raw_title=candidate.raw_title,
        raw_excerpt=candidate.raw_excerpt,
        signal_score=signal_score,
        status=status,
        discovered_at=candidate.discovered_at or datetime.now(UTC),
    )
    session.add(row)
    return row


async def get_by_status(
    session: AsyncSession, status: str, limit: int = 100
) -> list[CandidateURLRow]:
    result = await session.scalars(
        select(CandidateURLRow)
        .where(CandidateURLRow.status == status)
        .order_by(CandidateURLRow.signal_score.desc())
        .limit(limit)
    )
    return list(result)


def set_status(row: CandidateURLRow, status: str) -> None:
    row.status = status
