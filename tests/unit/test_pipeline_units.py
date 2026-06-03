"""Unit tests for pure pipeline logic — no network, no DB (R14).

Covers the deterministic pieces: the discovery classifier, the evidence verifier, and the
offline stub extractor. Adapter/network tests use VCR cassettes (added with the Celery
worker pool in Phase 3).
"""

from __future__ import annotations

import pytest

from airadar.agents.classifier import heuristic_signal
from airadar.llm.client import StubExtractor
from airadar.llm.schema import PricingModel
from airadar.llm.verifiers import quote_is_grounded
from airadar.sources.base import CandidateURL


def _cand(title: str, excerpt: str = "", signal: float = 0.0) -> CandidateURL:
    return CandidateURL(
        url="https://x.example", raw_title=title, raw_excerpt=excerpt, signal=signal
    )


class TestClassifier:
    def test_launch_of_ai_tool_scores_high(self) -> None:
        score = heuristic_signal(_cand("Show HN: an open-source AI agent for coding"))
        assert score >= 0.6

    def test_listicle_is_penalized(self) -> None:
        score = heuristic_signal(_cand("Top 10 best AI tools you should know"))
        assert score < 0.6

    def test_non_ai_scores_low(self) -> None:
        assert heuristic_signal(_cand("My weekend woodworking project")) < 0.4

    def test_empty_is_zero(self) -> None:
        assert heuristic_signal(_cand("")) == 0.0


class TestVerifier:
    def test_exact_substring_is_grounded(self) -> None:
        assert quote_is_grounded("free and open source", "This tool is free and open source.")

    def test_absent_quote_not_grounded(self) -> None:
        assert not quote_is_grounded("costs $999 enterprise", "A simple free tool.")

    def test_none_quote_not_grounded(self) -> None:
        assert not quote_is_grounded(None, "anything")


class TestStubExtractor:
    @pytest.mark.asyncio
    async def test_strips_show_hn_and_separator(self) -> None:
        enr = await StubExtractor().extract(
            title="Show HN: FooAI — an AI writing assistant",
            url="https://foo.example",
            text="FooAI is an AI writing assistant. It is free to use.",
        )
        assert enr.name == "FooAI"
        assert enr.canonical_url == "https://foo.example"
        assert len(enr.categories) >= 1

    @pytest.mark.asyncio
    async def test_detects_open_source_with_grounded_evidence(self) -> None:
        text = "Acme is open source and available on https://github.com/acme/acme."
        enr = await StubExtractor().extract(title="Acme", url="https://acme.example", text=text)
        assert enr.pricing_model is PricingModel.open_source
        assert enr.is_open_source is True
        assert enr.github_url == "https://github.com/acme/acme"
        assert quote_is_grounded(enr.pricing_evidence_quote, text)

    @pytest.mark.asyncio
    async def test_unknown_pricing_has_no_evidence(self) -> None:
        enr = await StubExtractor().extract(
            title="Mystery", url="https://m.example", text="A tool that does things."
        )
        assert enr.pricing_model is PricingModel.unknown
        assert enr.pricing_evidence_quote is None
