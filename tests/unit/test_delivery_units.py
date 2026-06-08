"""Unit tests for the Delivery stage (R5) — pure personalization + rendering, no DB."""

from __future__ import annotations

from airadar.delivery.personalization import (
    FeedItem,
    UserFilters,
    select_for_user,
)
from airadar.delivery.renderers import EmailRenderer


def _item(
    id: str,
    *,
    quality: int = 50,
    categories: list[str] | None = None,
    country: str | None = "US",
    pricing: str | None = "freemium",
    name: str | None = None,
) -> FeedItem:
    return FeedItem(
        id=id,
        name=name or f"Tool {id}",
        one_liner=f"does {id} things",
        canonical_url=f"https://{id}.example",
        pricing_model=pricing,
        country_hq=country,
        quality_score=quality,
        categories=categories or ["agents"],
    )


class TestPersonalization:
    def test_min_quality_filters_out_low_scores(self) -> None:
        items = [_item("a", quality=20), _item("b", quality=90)]
        sel = select_for_user(items, UserFilters(min_quality_score=50), min_tools=1)
        assert [i.id for i in sel.items] == ["b"]
        assert sel.widened is False

    def test_include_categories_requires_overlap(self) -> None:
        items = [_item("a", categories=["code"]), _item("b", categories=["voice"])]
        sel = select_for_user(
            items, UserFilters(include_categories=["voice"], min_quality_score=0), min_tools=1
        )
        assert [i.id for i in sel.items] == ["b"]

    def test_exclude_categories_drops_match(self) -> None:
        items = [_item("a", categories=["nsfw", "image"]), _item("b", categories=["image"])]
        sel = select_for_user(
            items, UserFilters(exclude_categories=["nsfw"], min_quality_score=0), min_tools=1
        )
        assert [i.id for i in sel.items] == ["b"]

    def test_country_include_excludes_unknown(self) -> None:
        items = [_item("a", country=None), _item("b", country="IN")]
        sel = select_for_user(
            items, UserFilters(include_countries=["IN"], min_quality_score=0), min_tools=1
        )
        assert [i.id for i in sel.items] == ["b"]

    def test_pricing_allow_filters(self) -> None:
        items = [_item("a", pricing="paid"), _item("b", pricing="open_source")]
        sel = select_for_user(
            items, UserFilters(pricing_allow=["open_source"], min_quality_score=0), min_tools=1
        )
        assert [i.id for i in sel.items] == ["b"]

    def test_widens_quality_floor_rather_than_send_few(self) -> None:
        # Only one tool clears the user's quality floor; widening surfaces the rest.
        items = [_item("a", quality=80), _item("b", quality=10), _item("c", quality=5)]
        sel = select_for_user(items, UserFilters(min_quality_score=50), min_tools=3)
        assert sel.widened is True
        assert {i.id for i in sel.items} == {"a", "b", "c"}

    def test_no_widening_when_enough_match(self) -> None:
        items = [_item("a", quality=80), _item("b", quality=70), _item("c", quality=60)]
        sel = select_for_user(items, UserFilters(min_quality_score=50), min_tools=3)
        assert sel.widened is False

    def test_caps_at_max_tools(self) -> None:
        items = [_item(str(n), quality=90) for n in range(40)]
        sel = select_for_user(items, UserFilters(min_quality_score=0), max_tools=30)
        assert len(sel.items) == 30

    def test_empty_when_nothing_matches_even_widened(self) -> None:
        items = [_item("a", categories=["code"])]
        sel = select_for_user(items, UserFilters(include_categories=["voice"]), min_tools=3)
        assert sel.items == []


class TestRenderer:
    def test_render_includes_tool_and_subject(self) -> None:
        items = [_item("alpha", name="Alpha AI")]
        out = EmailRenderer().render(items=items, widened=False)
        assert "Alpha AI" in out.html
        assert "Alpha AI" in out.text
        assert "1 new AI tool" in out.subject

    def test_widened_notice_appears(self) -> None:
        out = EmailRenderer().render(items=[_item("a")], widened=True)
        assert "widened" in out.html.lower()
        assert "widened" in out.text.lower()

    def test_plural_subject(self) -> None:
        out = EmailRenderer().render(items=[_item("a"), _item("b")], widened=False)
        assert "2 new AI tools" in out.subject
