"""Unit tests for source adapter mapping logic (R14) — pure, no network."""

from __future__ import annotations

from datetime import UTC, datetime

from airadar.sources.github import _to_candidate


def _item(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "html_url": "https://github.com/acme/cool-ai",
        "name": "cool-ai",
        "description": "An AI agent that does cool things.",
        "stargazers_count": 1234,
        "created_at": "2026-06-05T10:00:00Z",
    }
    base.update(overrides)
    return base


class TestGitHubMapper:
    def test_maps_core_fields(self) -> None:
        c = _to_candidate(_item())
        assert c is not None
        assert c.url == "https://github.com/acme/cool-ai"
        assert c.raw_title == "cool-ai"
        assert c.raw_excerpt == "An AI agent that does cool things."
        assert c.signal == 1234.0

    def test_parses_created_at_to_utc(self) -> None:
        c = _to_candidate(_item())
        assert c is not None
        assert c.discovered_at == datetime(2026, 6, 5, 10, 0, tzinfo=UTC)

    def test_missing_url_is_dropped(self) -> None:
        assert _to_candidate(_item(html_url="")) is None

    def test_missing_description_is_none(self) -> None:
        c = _to_candidate(_item(description=None))
        assert c is not None
        assert c.raw_excerpt is None

    def test_missing_stars_defaults_to_zero(self) -> None:
        item = _item()
        del item["stargazers_count"]
        c = _to_candidate(item)
        assert c is not None
        assert c.signal == 0.0
