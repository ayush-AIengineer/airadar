"""Source adapter contract.

Every data source implements :class:`SourceAdapter` (Architecture §4.1). One adapter
per file — no multi-source files. Adapters return normalized :class:`CandidateURL`
objects and never touch the database directly; persistence is the Discovery agent's job.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class CandidateURL(BaseModel):
    """A normalized candidate produced by a source adapter, pre-persistence."""

    url: str
    raw_title: str | None = None
    raw_excerpt: str | None = None
    # Source-native popularity signal (HN points, GH stars, PH votes) if available.
    signal: float | None = None
    discovered_at: datetime | None = None

    @property
    def url_hash(self) -> str:
        return hashlib.sha256(self.url.encode("utf-8")).hexdigest()


class SourceHealth(BaseModel):
    ok: bool
    detail: str = ""
    checked_at: datetime | None = None


@runtime_checkable
class SourceAdapter(Protocol):
    """Contract every source must implement."""

    source_id: str
    rate_limit_per_minute: int

    async def fetch_since(self, since: datetime) -> list[CandidateURL]: ...
    async def health_check(self) -> SourceHealth: ...
