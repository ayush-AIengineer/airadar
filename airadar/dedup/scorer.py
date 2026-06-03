"""Rule-based quality scorer (Architecture §4.4).

Transparent 0–100 score combining popularity signals and record completeness — no LLM,
no vibes. The spec's formula:

    25 * norm(github_stars_24h) + 20 * norm(hn_points) + 20 * norm(producthunt_votes)
  + 15 * has_clear_pricing + 10 * has_country + 10 * description_quality

Popularity inputs default to 0 when a source didn't provide them (threading per-source
popularity onto the tool record is a tracked follow-up — see ToolSignals). Tools scoring
< 30 are stored but excluded from default feeds (R4).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ToolSignals:
    """Inputs to the quality score for a single tool."""

    github_stars_24h: int = 0
    hn_points: int = 0
    producthunt_votes: int = 0
    has_clear_pricing: bool = False  # pricing_model known (not 'unknown')
    has_country: bool = False
    description_length: int = 0


def _norm_log(value: int, ceiling: int) -> float:
    """Log-normalize a count into [0, 1]; `ceiling` maps to ~1.0."""
    if value <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(ceiling))


def _description_quality(length: int) -> float:
    # 0 at empty, ramps to 1.0 around a 300+ char description.
    return min(1.0, length / 300.0)


def quality_score(signals: ToolSignals) -> int:
    score = (
        25 * _norm_log(signals.github_stars_24h, ceiling=2000)
        + 20 * _norm_log(signals.hn_points, ceiling=500)
        + 20 * _norm_log(signals.producthunt_votes, ceiling=1000)
        + 15 * (1.0 if signals.has_clear_pricing else 0.0)
        + 10 * (1.0 if signals.has_country else 0.0)
        + 10 * _description_quality(signals.description_length)
    )
    return round(max(0, min(100, score)))
