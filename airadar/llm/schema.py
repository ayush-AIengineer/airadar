"""Structured enrichment schema (Architecture §4.3).

Every LLM extraction must validate against :class:`ToolEnrichment`. Fields that can be
hallucinated carry an evidence quote so the verifier (R3) can confirm them against the
source text before they are trusted.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class PricingModel(StrEnum):
    free = "free"
    open_source = "open_source"
    freemium = "freemium"
    free_trial = "free_trial"
    paid = "paid"
    enterprise_only = "enterprise_only"
    unknown = "unknown"


class Category(StrEnum):
    """Canonical category taxonomy (seeded into the `categories` table)."""

    agents = "agents"
    code = "code"
    voice = "voice"
    image = "image"
    video = "video"
    audio = "audio"
    design = "design"
    writing = "writing"
    rag = "rag"
    data = "data"
    search = "search"
    productivity = "productivity"
    marketing = "marketing"
    research = "research"
    security = "security"
    other = "other"


class ToolEnrichment(BaseModel):
    """Canonical extracted record for one tool."""

    name: str = Field(..., max_length=120)
    canonical_url: str = Field(..., max_length=2000)
    one_liner: str = Field(..., max_length=200)
    description: str = Field(default="", max_length=1200)
    categories: list[Category] = Field(..., min_length=1, max_length=4)
    pricing_model: PricingModel
    pricing_evidence_quote: str | None = Field(default=None, max_length=300)
    starting_price_usd_monthly: float | None = None
    country_hq: str | None = Field(default=None, max_length=2)  # ISO 3166-1 alpha-2
    country_evidence: str | None = None
    launch_date_iso: date | None = None
    launch_date_evidence: str | None = None
    is_open_source: bool = False
    github_url: str | None = None
    tech_stack_mentioned: list[str] = Field(default_factory=list, max_length=10)
    social_handles: dict[str, str] = Field(default_factory=dict)
    confidence_score: float = Field(..., ge=0, le=1)
