"""Repository for the delivery audit log (one aggregate per file — R6).

The ``digest_log`` unique constraint on (user_id, channel, sent_on) is the idempotency
guard (R5): a retried Delivery run must never double-send. :func:`already_sent` is the
cheap pre-check; the constraint is the backstop if two workers race.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.db.models import DigestLog


async def already_sent(
    session: AsyncSession, *, user_id: uuid.UUID, channel: str, on_date: date
) -> bool:
    existing = await session.scalar(
        select(DigestLog.id).where(
            DigestLog.user_id == user_id,
            DigestLog.channel == channel,
            DigestLog.sent_on == on_date,
        )
    )
    return existing is not None


def record(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    channel: str,
    tool_ids: list[str],
    on_date: date,
    sent_at: datetime,
    delivery_status: str,
) -> None:
    session.add(
        DigestLog(
            user_id=user_id,
            channel=channel,
            tool_ids=tool_ids,
            sent_on=on_date,
            sent_at=sent_at,
            delivery_status=delivery_status,
        )
    )
