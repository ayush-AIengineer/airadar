"""Enrichment extractor backends (Architecture §4.3).

Two interchangeable backends behind one interface:

- :class:`StubExtractor` — deterministic, offline, zero-cost. Runs the full pipeline with
  no API key. Pulls evidence quotes verbatim from the text so the verifier is meaningful.
- :class:`AnthropicExtractor` — real Claude (Sonnet) via Instructor, with the stable
  system prompt marked for prompt caching (Architecture §4.3 / §11). Lazy-imports
  ``anthropic`` so the base install never needs it.

:func:`get_extractor` picks the backend from settings (key present → real, else stub).
Per R13, the cheap classifier/verifier never use Sonnet — only enrichment does.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from airadar.config import Settings
from airadar.llm.schema import Category, PricingModel, ToolEnrichment

_PROMPT_DIR = Path(__file__).parent / "prompts"
ENRICHMENT_PROMPT_VERSION = "enrichment_v1"


def load_prompt(version: str = ENRICHMENT_PROMPT_VERSION) -> str:
    return (_PROMPT_DIR / f"{version}.txt").read_text(encoding="utf-8")


class Extractor(Protocol):
    prompt_version: str

    async def extract(self, *, title: str, url: str, text: str) -> ToolEnrichment: ...


# ── Deterministic offline stub ───────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.agents: ("agent", "autonomous", "assistant"),
    Category.code: ("code", "coding", "developer", "ide", "programming"),
    Category.voice: ("voice", "speech", "tts", "transcription"),
    Category.image: ("image", "text-to-image", "photo", "diffusion"),
    Category.video: ("video", "film", "animation"),
    Category.audio: ("audio", "music", "sound"),
    Category.design: ("design", "ui", "figma", "logo"),
    Category.writing: ("writing", "writer", "blog", "essay", "content"),
    Category.rag: ("rag", "retrieval", "knowledge base", "embeddings"),
    Category.data: ("data", "analytics", "database", "sql"),
    Category.search: ("search", "discovery"),
    Category.productivity: ("productivity", "workflow", "automation", "notes"),
    Category.marketing: ("marketing", "seo", "ads", "campaign"),
    Category.research: ("research", "paper", "science", "genome"),
    Category.security: ("security", "privacy", "auth"),
}

_PRICE_RE = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)")
# Repo path must end on a word char or hyphen so trailing punctuation isn't captured.
_GITHUB_RE = re.compile(r"https?://github\.com/[\w-]+/[\w.-]*[\w-]")
_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]")


def _strip_prefix(title: str) -> str:
    title = re.sub(r"^\s*Show HN:\s*", "", title, flags=re.IGNORECASE)
    # Cut the product name from its tagline: "Foo: does X", "Foo — does X", "Foo, the X".
    # Colon/dash/pipe may be tight ("VibeOS:") or spaced; comma needs a trailing space.
    return re.split(r"\s*[—–|:]\s+|\s+[-]\s+|,\s+", title, maxsplit=1)[0].strip() or title.strip()


def _best_one_liner(text: str, fallback: str) -> str:
    """First *substantial* sentence (≥4 words, ≥24 chars) — skips fragments like 'persist.'."""
    for sentence in _SENTENCE_RE.findall(text):
        s: str = sentence.strip()
        if len(s) >= 24 and len(s.split()) >= 4:
            return s[:180]
    clean = fallback.strip()
    return (clean if len(clean) >= 12 else text.strip()[:180]) or "An AI tool."


def _detect_categories(title: str, text: str) -> list[Category]:
    """Weighted category tagging: title hits count heavily; a lone body mention isn't enough.

    Avoids the over-tagging where any stray keyword in the page body slapped a category on
    everything. A category needs a title hit (weight 3) or ≥2 body mentions to qualify.
    """
    title_low = title.lower()
    body_low = text.lower()
    scores: dict[Category, int] = {}
    for cat, kws in _CATEGORY_KEYWORDS.items():
        score = 0
        for kw in kws:
            if kw in title_low:
                score += 3
            score += min(body_low.count(kw), 2)
        if score:
            scores[cat] = score
    ranked = sorted(scores, key=lambda c: scores[c], reverse=True)
    qualified = [c for c in ranked if scores[c] >= 2][:3]
    if qualified:
        return qualified
    return ranked[:1] or [Category.other]


def _detect_pricing(text: str) -> tuple[PricingModel, str | None, float | None]:
    low = text.lower()
    price_match = _PRICE_RE.search(text)
    price = float(price_match.group(1)) if price_match else None
    if "open source" in low or "open-source" in low:
        return PricingModel.open_source, _quote_around(text, "open source") or _quote_around(
            text, "open-source"
        ), price
    if "free trial" in low:
        return PricingModel.free_trial, _quote_around(text, "free trial"), price
    if "freemium" in low:
        return PricingModel.freemium, _quote_around(text, "freemium"), price
    if price_match is not None:
        return PricingModel.paid, _quote_around(text, price_match.group(0)), price
    if re.search(r"\bfree\b", low):
        return PricingModel.free, _quote_around(text, "free"), price
    return PricingModel.unknown, None, None


def _quote_around(text: str, needle: str, width: int = 140) -> str | None:
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return None
    start = max(0, idx - width // 2)
    end = min(len(text), idx + len(needle) + width // 2)
    return text[start:end].strip()[:300]


class StubExtractor:
    """Deterministic, key-free extractor for local/offline runs and tests."""

    prompt_version = "stub_v1"

    async def extract(self, *, title: str, url: str, text: str) -> ToolEnrichment:
        title = title or "Untitled"
        name = _strip_prefix(title)[:120]
        pricing, pricing_quote, price = _detect_pricing(text)
        github_match = _GITHUB_RE.search(text)
        is_oss = pricing is PricingModel.open_source or github_match is not None
        return ToolEnrichment(
            name=name,
            canonical_url=url,
            one_liner=_best_one_liner(text, fallback=title),
            description=text.strip()[:1200],
            categories=_detect_categories(title, text),
            pricing_model=pricing,
            pricing_evidence_quote=pricing_quote,
            starting_price_usd_monthly=price if pricing is PricingModel.paid else None,
            country_hq=None,  # stub never guesses country — real backend runs the cascade
            country_evidence=None,
            launch_date_iso=None,
            is_open_source=is_oss,
            github_url=github_match.group(0) if github_match else None,
            confidence_score=0.5,
        )


# ── Real Anthropic backend ───────────────────────────────────────────────────


class AnthropicExtractor:
    """Claude Sonnet extractor via Instructor, with prompt caching on the system prefix."""

    prompt_version = ENRICHMENT_PROMPT_VERSION

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._system = load_prompt(self.prompt_version)

    async def extract(self, *, title: str, url: str, text: str) -> ToolEnrichment:
        import anthropic
        import instructor

        client = instructor.from_anthropic(
            anthropic.AsyncAnthropic(api_key=self._settings.anthropic_api_key)
        )
        user_content = (
            f"<title>{title}</title>\n<url>{url}</url>\n"
            f"<page_text>\n{text[:24000]}\n</page_text>"
        )
        result: ToolEnrichment = await client.chat.completions.create(
            model=self._settings.enrichment_model,
            max_tokens=1500,
            response_model=ToolEnrichment,
            system=[
                {
                    "type": "text",
                    "text": self._system,
                    "cache_control": {"type": "ephemeral"},  # cache the stable prefix
                }
            ],
            messages=[{"role": "user", "content": user_content}],
        )
        return result


def get_extractor(settings: Settings) -> Extractor:
    if settings.anthropic_api_key:
        return AnthropicExtractor(settings)
    return StubExtractor()
