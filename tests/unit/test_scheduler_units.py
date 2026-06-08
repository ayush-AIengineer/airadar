"""Unit tests for the scheduler due-check (R9) — pure, deterministic (now is injected)."""

from __future__ import annotations

from datetime import UTC, datetime

from airadar.scheduler.jobs import user_is_due

_DAILY_8AM = "0 8 * * *"


class TestUserIsDue:
    def test_due_after_local_fire_time(self) -> None:
        # 08:30 IST (= 03:00 UTC) — the 08:00 IST fire has passed today.
        now = datetime(2026, 6, 7, 3, 0, tzinfo=UTC)
        assert user_is_due(_DAILY_8AM, "Asia/Kolkata", now) is True

    def test_not_due_before_local_fire_time(self) -> None:
        # 07:30 IST (= 02:00 UTC) — before the 08:00 IST fire.
        now = datetime(2026, 6, 7, 2, 0, tzinfo=UTC)
        assert user_is_due(_DAILY_8AM, "Asia/Kolkata", now) is False

    def test_timezone_matters(self) -> None:
        # 12:00 UTC: already past 08:00 in New York? 12:00 UTC = 08:00 EDT → due.
        now = datetime(2026, 6, 7, 12, 0, tzinfo=UTC)
        assert user_is_due(_DAILY_8AM, "America/New_York", now) is True
        # Same instant is 05:00 in Los Angeles → not yet due.
        assert user_is_due(_DAILY_8AM, "America/Los_Angeles", now) is False

    def test_unknown_timezone_falls_back_to_utc(self) -> None:
        now = datetime(2026, 6, 7, 9, 0, tzinfo=UTC)  # 09:00 UTC, past 08:00 UTC
        assert user_is_due(_DAILY_8AM, "Not/AZone", now) is True

    def test_hourly_cron_always_due_within_the_day(self) -> None:
        now = datetime(2026, 6, 7, 0, 30, tzinfo=UTC)  # 00:30, last fire 00:00 today
        assert user_is_due("0 * * * *", "UTC", now) is True
