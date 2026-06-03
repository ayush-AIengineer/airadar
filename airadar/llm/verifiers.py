"""Evidence verifier — anti-hallucination second pass (Architecture §4.3).

Every populated, evidence-bearing field must be backed by a quote that actually appears
in the source text. Offline, we verify by checking the quote is grounded in the page
(substring / high token overlap). With a key, the Haiku verifier (TODO) replaces this with
a semantic "does quote X support value Y?" check — cheap model only, never Sonnet (R13).
"""

from __future__ import annotations

import re


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def quote_is_grounded(quote: str | None, source_text: str, min_overlap: float = 0.6) -> bool:
    """True if the evidence quote is supported by the source text.

    Exact (normalized) substring match passes immediately. Otherwise we accept the quote
    if a strong majority of its words appear in the source (tolerates whitespace/clipping).
    """
    if not quote:
        return False
    norm_quote = _normalize(quote)
    norm_source = _normalize(source_text)
    if norm_quote in norm_source:
        return True
    words = [w for w in norm_quote.split() if len(w) > 2]
    if not words:
        return False
    source_words = set(norm_source.split())
    hits = sum(1 for w in words if w in source_words)
    return hits / len(words) >= min_overlap
