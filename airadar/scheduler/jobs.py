"""Scheduler (Architecture §3.2, R9) — fires digests at each user's local time.

A single APScheduler tick wakes every ``scheduler_tick_minutes`` and asks: which users
are *due* right now? "Due" means the user's ``digest_cron`` has already fired today in
their own timezone. The Delivery agent's per-day idempotency guarantees that even if the
tick runs many times after the fire time, each user is sent at most once per day.

The due-check (:func:`user_is_due`) is pure and unit-tested; APScheduler is only the
clock that drives it. APScheduler is lazy-imported so importing this module (e.g. for the
pure due-check) never requires the scheduler dependency group.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from croniter import croniter
from loguru import logger

from airadar.agents.delivery import resolve_tz, run_delivery
from airadar.config import get_settings
from airadar.db.repositories import users as users_repo
from airadar.db.session import session_scope


def user_is_due(cron: str, timezone: str, now_utc: datetime) -> bool:
    """True if the user's cron has already fired today in their timezone.

    ``now_utc`` is passed in (not read from the clock) so this is deterministic and
    testable. An unknown timezone falls back to UTC rather than skipping the user.
    """
    now_local = now_utc.astimezone(resolve_tz(timezone))
    # The first scheduled fire on today's local date. The user is due once that moment has
    # arrived (>= handles landing exactly on the fire time). Idempotency keeps it once/day.
    day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    first_fire_today = croniter(cron, day_start - timedelta(microseconds=1)).get_next(datetime)
    return bool(
        first_fire_today.date() == now_local.date() and first_fire_today <= now_local
    )


async def deliver_due(now_utc: datetime | None = None) -> None:
    """One scheduler tick: deliver to every subscriber whose digest time has passed today."""
    now = now_utc or datetime.now(UTC)
    async with session_scope() as session:
        subscribers = await users_repo.list_subscribers(session)
        due = {
            u.id
            for u in subscribers
            if u.preferences is not None
            and user_is_due(u.preferences.digest_cron, u.timezone, now)
        }
        if not due:
            logger.debug("Scheduler tick: no users due at {}", now.isoformat())
            return
        logger.info("Scheduler tick: {} user(s) due", len(due))
        # on_date=None → run_delivery keys idempotency by each user's local date.
        await run_delivery(session, only_user_ids=due)


def run_scheduler() -> None:
    """Start the blocking scheduler loop (CLI entrypoint)."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        deliver_due,
        IntervalTrigger(minutes=settings.scheduler_tick_minutes),
        id="deliver_due",
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        "Scheduler started — checking for due digests every {} min", settings.scheduler_tick_minutes
    )
    scheduler.start()
    try:
        import asyncio

        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover — manual stop
        logger.info("Scheduler stopped")
