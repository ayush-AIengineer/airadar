"""Hacker News source adapter (Architecture §5.1, Tier A).

Uses the Algolia HN Search API — free, keyless. We query recent `Show HN` and
AI-related stories. Chosen as the first adapter because it needs no credentials,
which lets the Phase 1 skeleton run end-to-end with zero setup.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from airadar.sources.base import CandidateURL, SourceAdapter, SourceHealth

_ALGOLIA_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
_QUERY_TAGS = "story"
# Stories whose title/text mention these are likely AI tool launches.
_QUERY = "AI"


class HackerNewsAdapter(SourceAdapter):
    source_id = "hackernews"
    rate_limit_per_minute = 60  # Algolia is generous; stay polite.

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def _get(self, params: dict[str, str | int]) -> dict[str, object]:
        if self._client is not None:
            resp = await self._client.get(_ALGOLIA_SEARCH, params=params)
            resp.raise_for_status()
            return dict(resp.json())
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(_ALGOLIA_SEARCH, params=params)
            resp.raise_for_status()
            return dict(resp.json())

    async def fetch_since(self, since: datetime) -> list[CandidateURL]:
        since_ts = int(since.replace(tzinfo=since.tzinfo or UTC).timestamp())
        data = await self._get(
            {
                "query": _QUERY,
                "tags": _QUERY_TAGS,
                "numericFilters": f"created_at_i>{since_ts}",
                "hitsPerPage": 50,
            }
        )
        hits = data.get("hits")
        candidates: list[CandidateURL] = []
        for hit in hits if isinstance(hits, list) else []:
            if not isinstance(hit, dict):
                continue
            # Prefer the external story URL; fall back to the HN discussion permalink.
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            if not url:
                continue
            created_i = hit.get("created_at_i")
            discovered = (
                datetime.fromtimestamp(created_i, tz=UTC)
                if isinstance(created_i, int)
                else None
            )
            candidates.append(
                CandidateURL(
                    url=str(url),
                    raw_title=hit.get("title"),
                    raw_excerpt=(hit.get("story_text") or "")[:500] or None,
                    signal=float(hit.get("points") or 0),
                    discovered_at=discovered,
                )
            )
        return candidates

    async def health_check(self) -> SourceHealth:
        try:
            await self._get({"query": "test", "tags": "story", "hitsPerPage": 1})
            return SourceHealth(ok=True, detail="algolia reachable")
        except Exception as exc:  # noqa: BLE001 — health check reports any failure
            return SourceHealth(ok=False, detail=str(exc))
