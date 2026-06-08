"""Email rendering (Architecture §4.5).

Renders the digest through Jinja2 templates (R5: render via the template engine, never
string concatenation). MJML responsive HTML is a Phase 3 upgrade — the channel-specific
HTML/text split here keeps that swap local to this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from airadar.delivery.personalization import FeedItem

_TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    html: str
    text: str


@lru_cache(maxsize=1)
def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(_TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


class EmailRenderer:
    """Renders the daily digest into subject + HTML + plain-text."""

    def render(self, *, items: list[FeedItem], widened: bool) -> RenderedEmail:
        n = len(items)
        subject = f"AIRadar — {n} new AI tool{'s' if n != 1 else ''} today"
        ctx = {"items": items, "widened": widened, "count": n}
        html = _env().get_template("digest.html.j2").render(**ctx)
        text = _env().get_template("digest.txt.j2").render(**ctx)
        return RenderedEmail(subject=subject, html=html, text=text)
