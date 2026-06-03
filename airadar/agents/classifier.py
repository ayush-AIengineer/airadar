"""Cheap candidate classifier for the Discovery stage (Architecture §4.1).

Labels each candidate with a ``signal_score`` in [0, 1] estimating "is this a newly
launched AI tool?". Per R1/R13, classification must use the **cheapest** path that works
— never Sonnet.

Phase 1 ships a deterministic keyword heuristic so the pipeline runs with zero API keys
and zero cost. When an Anthropic key is configured, the Haiku path (TODO below) replaces
the heuristic for higher precision. The interface stays identical either way.
"""

from __future__ import annotations

from airadar.sources.base import CandidateURL

# Signals that the item is about AI, and that it is a *launch* (not commentary/listicle).
_AI_TERMS = (
    "ai",
    "llm",
    "gpt",
    "agent",
    "rag",
    "model",
    "machine learning",
    "neural",
    "diffusion",
    "embedding",
)
_LAUNCH_TERMS = (
    "show hn",
    "launch",
    "launching",
    "introducing",
    "we built",
    "released",
    "release",
    "new tool",
    "built a",
    "i made",
    "open source",
    "open-source",
)
# Anti-signals: listicles / commentary that pass the AI filter but aren't launches.
_NOISE_TERMS = (
    "top 10",
    "best ai tools",
    "you should know",
    "a guide to",
    "vs ",
    "how to use",
)


def heuristic_signal(candidate: CandidateURL) -> float:
    """Deterministic 0..1 score from title/excerpt keyword matches."""
    text = f"{candidate.raw_title or ''} {candidate.raw_excerpt or ''}".lower()
    if not text.strip():
        return 0.0

    has_ai = any(term in text for term in _AI_TERMS)
    if not has_ai:
        return 0.1  # almost certainly not relevant

    score = 0.5  # AI-related baseline
    if any(term in text for term in _LAUNCH_TERMS):
        score += 0.35
    if any(term in text for term in _NOISE_TERMS):
        score -= 0.4
    # Source-native popularity nudges confidence up a little.
    if candidate.signal and candidate.signal >= 10:
        score += 0.1

    return max(0.0, min(1.0, score))


class SignalClassifier:
    """Scores candidates. Heuristic today; Haiku-backed when a key is present."""

    def __init__(self, use_llm: bool = False) -> None:
        self.use_llm = use_llm

    async def score(self, candidate: CandidateURL) -> float:
        if self.use_llm:
            # TODO(R3): lazy-import anthropic and call the Haiku classifier here with the
            # cached system prompt. Falls back to the heuristic on any error. Never Sonnet.
            return heuristic_signal(candidate)
        return heuristic_signal(candidate)
