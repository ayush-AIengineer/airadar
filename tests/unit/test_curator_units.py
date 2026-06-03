"""Unit tests for the Curator/Dedup logic (R4) — pure functions + embedder."""

from __future__ import annotations

import math

import pytest

from airadar.agents.curator import (
    _MULTI_TENANT_DOMAINS,
    _normalize_name,
    _registered_domain,
)
from airadar.dedup.embeddings import HashingEmbedder
from airadar.dedup.scorer import ToolSignals, quality_score


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class TestScorer:
    def test_empty_record_scores_low(self) -> None:
        assert quality_score(ToolSignals()) == 0

    def test_pricing_and_country_and_desc(self) -> None:
        s = ToolSignals(has_clear_pricing=True, has_country=True, description_length=300)
        # 15 + 10 + 10 = 35
        assert quality_score(s) == 35

    def test_popularity_dominates(self) -> None:
        viral = ToolSignals(hn_points=500, github_stars_24h=2000, producthunt_votes=1000)
        assert quality_score(viral) >= 60

    def test_score_capped_at_100(self) -> None:
        maxed = ToolSignals(
            github_stars_24h=10_000,
            hn_points=5_000,
            producthunt_votes=10_000,
            has_clear_pricing=True,
            has_country=True,
            description_length=1000,
        )
        assert quality_score(maxed) <= 100


class TestDedupHelpers:
    def test_registered_domain(self) -> None:
        assert _registered_domain("https://www.foo.example.com/path?x=1") == "example.com"

    def test_github_is_multi_tenant(self) -> None:
        assert _registered_domain("https://github.com/a/b") in _MULTI_TENANT_DOMAINS

    def test_normalize_name_strips_punctuation_and_case(self) -> None:
        assert _normalize_name("Foo-AI 2.0!") == "fooai20"


class TestHashingEmbedder:
    @pytest.mark.asyncio
    async def test_deterministic(self) -> None:
        e = HashingEmbedder()
        assert await e.embed("an ai writing tool") == await e.embed("an ai writing tool")

    @pytest.mark.asyncio
    async def test_identical_text_is_near_duplicate(self) -> None:
        e = HashingEmbedder()
        v1 = await e.embed("AI resume builder that writes your CV")
        v2 = await e.embed("AI resume builder that writes your CV")
        assert _cosine(v1, v2) > 0.99

    @pytest.mark.asyncio
    async def test_unrelated_text_is_not_near_duplicate(self) -> None:
        e = HashingEmbedder()
        v1 = await e.embed("AI resume builder career tool")
        v2 = await e.embed("quantum physics simulation engine")
        assert _cosine(v1, v2) < 0.88
