"""Delivery agent (Architecture §4.5) — the fifth and final pipeline stage.

Gets the right tools to the right user in the right format. For each subscriber it loads
recent published tools, applies their filters (widening one step rather than sending an
empty digest), renders an email, sends it, and records the send.

Idempotency is sacred (R5): a re-run on the same day never double-sends — guarded by the
``digest_log`` unique constraint and a cheap pre-check. Phase 2 ships the email channel;
Telegram/Slack/RSS plug into the same loop later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.config import get_settings
from airadar.db.models import PipelineRun, Tool
from airadar.db.repositories import digests as digest_repo
from airadar.db.repositories import tools as tools_repo
from airadar.db.repositories import users as users_repo
from airadar.delivery.email import get_email_sender
from airadar.delivery.personalization import FeedItem, UserFilters, select_for_user
from airadar.delivery.renderers import EmailRenderer

_SUPPORTED_CHANNELS = frozenset({"email"})  # Phase 2: email only (R5; others land later)


def resolve_tz(timezone: str) -> ZoneInfo:
    """User timezone → ZoneInfo, falling back to UTC on an unknown string (never drop a user)."""
    try:
        return ZoneInfo(timezone)
    except Exception:  # noqa: BLE001 — a bad tz string must not crash the batch
        logger.warning("Unknown timezone {!r}; falling back to UTC", timezone)
        return ZoneInfo("UTC")


@dataclass
class DeliverResult:
    users: int
    digests_sent: int
    tools_delivered: int
    widened: int
    skipped_idempotent: int
    skipped_empty: int


def _to_feed_item(tool: Tool) -> FeedItem:
    return FeedItem(
        id=str(tool.id),
        name=tool.name,
        one_liner=tool.one_liner,
        canonical_url=tool.canonical_url,
        pricing_model=tool.pricing_model,
        country_hq=tool.country_hq,
        quality_score=tool.quality_score or 0,
        categories=[c.slug for c in tool.categories],
    )


async def run_delivery(
    session: AsyncSession,
    *,
    on_date: date | None = None,
    limit: int | None = None,
    only_user_ids: set[uuid.UUID] | None = None,
) -> DeliverResult:
    """Deliver digests.

    ``only_user_ids`` restricts the run to a specific set of subscribers (the scheduler
    passes the users that are due now); ``None`` means all subscribers. ``limit`` caps how
    many subscribers are processed this run.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    sender = get_email_sender(settings)
    renderer = EmailRenderer()

    since = now - timedelta(hours=settings.digest_lookback_hours)
    candidates = await tools_repo.list_feed_candidates(session, since)
    feed = [_to_feed_item(t) for t in candidates]

    subscribers = await users_repo.list_subscribers(session)
    if only_user_ids is not None:
        subscribers = [u for u in subscribers if u.id in only_user_ids]
    if limit is not None:
        subscribers = subscribers[:limit]
    run = PipelineRun(stage="delivery", status="running", items_in=len(subscribers))
    session.add(run)

    digests_sent = tools_delivered = widened = skipped_idempotent = skipped_empty = 0
    try:
        for user in subscribers:
            prefs = user.preferences
            if prefs is None:
                continue
            # Idempotency is keyed by the user's *local* calendar date, so a far-west user
            # near midnight isn't double-bucketed against UTC. ``on_date`` overrides (tests).
            day = on_date or now.astimezone(resolve_tz(user.timezone)).date()
            for channel in prefs.channels:
                if channel not in _SUPPORTED_CHANNELS:
                    logger.debug("Channel {!r} not supported yet; skipping", channel)
                    continue
                if await digest_repo.already_sent(
                    session, user_id=user.id, channel=channel, on_date=day
                ):
                    skipped_idempotent += 1
                    continue

                filters = UserFilters(
                    include_categories=list(prefs.include_categories),
                    exclude_categories=list(prefs.exclude_categories),
                    include_countries=list(prefs.include_countries),
                    exclude_countries=list(prefs.exclude_countries),
                    pricing_allow=list(prefs.pricing_allow),
                    min_quality_score=prefs.min_quality_score,
                )
                selection = select_for_user(
                    feed,
                    filters,
                    max_tools=settings.digest_max_tools,
                    min_tools=settings.digest_min_tools,
                )
                if not selection.items:
                    # Never send an empty digest; leave it unrecorded so a later run
                    # (after more tools are curated) can still deliver today.
                    skipped_empty += 1
                    continue

                rendered = renderer.render(items=selection.items, widened=selection.widened)
                status = await sender.send(
                    to=user.email, sender=settings.email_from, email=rendered
                )
                digest_repo.record(
                    session,
                    user_id=user.id,
                    channel=channel,
                    tool_ids=[it.id for it in selection.items],
                    on_date=day,
                    sent_at=datetime.now(UTC),
                    delivery_status=status,
                )
                if status == "sent":
                    digests_sent += 1
                    tools_delivered += len(selection.items)
                    if selection.widened:
                        widened += 1

        run.status = "ok"
    except Exception as exc:
        run.status = "error"
        run.error_message = str(exc)
        logger.exception("Delivery failed")
        raise
    finally:
        run.finished_at = datetime.now(UTC)
        run.items_out = digests_sent

    logger.info(
        "Delivery: users={} digests_sent={} tools_delivered={} widened={} "
        "skipped_idempotent={} skipped_empty={}",
        len(subscribers),
        digests_sent,
        tools_delivered,
        widened,
        skipped_idempotent,
        skipped_empty,
    )
    return DeliverResult(
        users=len(subscribers),
        digests_sent=digests_sent,
        tools_delivered=tools_delivered,
        widened=widened,
        skipped_idempotent=skipped_idempotent,
        skipped_empty=skipped_empty,
    )
