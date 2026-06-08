"""Per-user feed selection (Architecture §4.5) — pure, no I/O, fully unit-testable.

The Delivery agent converts ORM ``Tool`` rows into :class:`FeedItem`s and applies these
filters. Keeping the logic pure means the personalization rules (including the "widen
rather than send empty" rule, R5) are tested without a database.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FeedItem:
    """A delivery-ready view of a published tool."""

    id: str
    name: str
    one_liner: str | None
    canonical_url: str
    pricing_model: str | None
    country_hq: str | None
    quality_score: int
    categories: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UserFilters:
    """The subset of a user's preferences that drives feed selection."""

    include_categories: list[str] = field(default_factory=list)
    exclude_categories: list[str] = field(default_factory=list)
    include_countries: list[str] = field(default_factory=list)
    exclude_countries: list[str] = field(default_factory=list)
    pricing_allow: list[str] = field(default_factory=list)
    min_quality_score: int = 30


@dataclass(frozen=True)
class Selection:
    """Result of selecting a user's digest items."""

    items: list[FeedItem]
    widened: bool


def _matches(item: FeedItem, f: UserFilters, *, min_quality: int) -> bool:
    if item.quality_score < min_quality:
        return False
    cats = set(item.categories)
    if f.include_categories and cats.isdisjoint(f.include_categories):
        return False
    if f.exclude_categories and not cats.isdisjoint(f.exclude_categories):
        return False
    country = item.country_hq
    if f.include_countries and (country is None or country not in f.include_countries):
        return False
    if f.exclude_countries and country in f.exclude_countries:
        return False
    if f.pricing_allow and (
        item.pricing_model is None or item.pricing_model not in f.pricing_allow
    ):
        return False
    return True


def select_for_user(
    items: list[FeedItem],
    filters: UserFilters,
    *,
    max_tools: int = 30,
    min_tools: int = 3,
) -> Selection:
    """Pick a user's digest items.

    Applies the user's filters. If fewer than ``min_tools`` match, widen by **one step**
    — drop the quality floor to 0 (surface low-signal tools) rather than send an empty or
    near-empty digest (R5). Items are assumed pre-sorted best-first; capped at ``max_tools``.
    """
    matched = [it for it in items if _matches(it, filters, min_quality=filters.min_quality_score)]
    widened = False
    if len(matched) < min_tools and filters.min_quality_score > 0:
        widened_matches = [it for it in items if _matches(it, filters, min_quality=0)]
        if len(widened_matches) > len(matched):
            matched = widened_matches
            widened = True
    return Selection(items=matched[:max_tools], widened=widened)
