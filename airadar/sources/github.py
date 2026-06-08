"""GitHub source adapter (Architecture §5.1, Tier A).

Uses the GitHub Search API — free and keyless (an optional ``AIRADAR_GITHUB_TOKEN`` only
raises rate limits, it isn't required). Finds recently-created repositories tagged with
the ``ai`` topic, ranked by stars, as candidate AI-tool launches. One adapter per file (R1).
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from airadar.config import get_settings
from airadar.sources.base import CandidateURL, SourceAdapter, SourceHealth

_SEARCH = "https://api.github.com/search/repositories"
_BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "AIRadar-Bot/1.0 (+https://airadar.example/bot)",
}


def _to_candidate(item: dict[str, object]) -> CandidateURL | None:
    """Map one GitHub repo object to a normalized CandidateURL (pure, unit-tested)."""
    url = item.get("html_url")
    if not url:
        return None
    name = item.get("name")
    description = item.get("description")
    created = item.get("created_at")
    discovered: datetime | None = None
    if isinstance(created, str):
        try:
            discovered = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            discovered = None
    return CandidateURL(
        url=str(url),
        raw_title=str(name) if name else None,
        raw_excerpt=(str(description)[:500] or None) if description else None,
        signal=float(item.get("stargazers_count") or 0),  # type: ignore[arg-type]
        discovered_at=discovered,
    )


class GitHubAdapter(SourceAdapter):
    source_id = "github"
    rate_limit_per_minute = 10  # unauthenticated Search API limit; a token raises this.

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    def _headers(self) -> dict[str, str]:
        headers = dict(_BASE_HEADERS)
        token = get_settings().github_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _get(self, params: dict[str, str | int]) -> dict[str, object]:
        headers = self._headers()
        if self._client is not None:
            resp = await self._client.get(_SEARCH, params=params, headers=headers)
            resp.raise_for_status()
            return dict(resp.json())
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(_SEARCH, params=params, headers=headers)
            resp.raise_for_status()
            return dict(resp.json())

    async def fetch_since(self, since: datetime) -> list[CandidateURL]:
        since_date = since.astimezone(UTC).date().isoformat()
        data = await self._get(
            {
                "q": f"topic:ai created:>{since_date}",
                "sort": "stars",
                "order": "desc",
                "per_page": 30,
            }
        )
        items = data.get("items")
        candidates: list[CandidateURL] = []
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                candidate = _to_candidate(item)
                if candidate is not None:
                    candidates.append(candidate)
        return candidates

    async def health_check(self) -> SourceHealth:
        try:
            await self._get({"q": "topic:ai", "per_page": 1})
            return SourceHealth(ok=True, detail="github search reachable")
        except Exception as exc:  # noqa: BLE001 — health check reports any failure
            return SourceHealth(ok=False, detail=str(exc))
