"""Export curated tools from SQLite to a JSON file the frontend can consume.

A bridge until the FastAPI backend (Architecture §10) exists: the Next.js dashboard reads
this static file today, and will swap to ``GET /api/v1/tools`` with the same shape later.

    uv run python scripts/export_tools_json.py
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import tldextract

from airadar.db.models import Tool
from airadar.db.repositories import tools as tools_repo
from airadar.db.session import session_scope

_OUT = Path("frontend/public/data/tools.json")

# Domains that publish *articles about* AI, not AI products. Records on these are almost
# always news/commentary that slipped through discovery — never publish them.
_NON_PRODUCT_DOMAINS = frozenset(
    {
        "substack.com",
        "medium.com",
        "nytimes.com",
        "theverge.com",
        "techcrunch.com",
        "wired.com",
        "forbes.com",
        "bloomberg.com",
        "reuters.com",
        "news.ycombinator.com",
        "ycombinator.com",
        "reddit.com",
        "youtube.com",
        "wikipedia.org",
    }
)


def _registered_domain(url: str) -> str:
    ext = tldextract.extract(url)
    return f"{ext.domain}.{ext.suffix}".lower().strip(".")


# Finance / news / commentary language — a product one-liner never reads like this.
_NEWS_CONTENT_RE = re.compile(
    r"\b(s&p|nasdaq|dow jones|stocks?|shares|billion|trillion|earnings|valuation|"
    r"investors?|funding|raised|lawsuit|\d+\s?%)\b",
    re.IGNORECASE,
)


def _is_publishable(t: Tool) -> bool:
    """Hard quality gate for the public snapshot. When unsure, exclude (R15: protect trust)."""
    name = (t.name or "").strip()
    one_liner = (t.one_liner or "").strip()
    # Headline-like names are articles, not products.
    if not name or len(name) > 64 or len(name.split()) > 9:
        return False
    # A real product has a usable one-liner that doesn't read like finance/news prose.
    if len(one_liner) < 24:
        return False
    if _NEWS_CONTENT_RE.search(f"{name} {one_liner}"):
        return False
    # Must come from a product site, not a news/aggregator domain.
    if _registered_domain(t.canonical_url) in _NON_PRODUCT_DOMAINS:
        return False
    return True


async def _fetch() -> list[Tool]:
    async with session_scope() as session:
        return await tools_repo.list_feed_candidates(
            session, datetime.now(UTC) - timedelta(days=3650)
        )


def main() -> None:
    rows = asyncio.run(_fetch())
    publishable = [t for t in rows if _is_publishable(t)]
    dropped = len(rows) - len(publishable)

    tools = [
        {
            "id": str(t.id),
            "name": t.name,
            "url": t.canonical_url,
            "oneLiner": t.one_liner,
            "description": (t.description or "")[:400],
            "pricing": t.pricing_model or "unknown",
            "country": t.country_hq,
            "quality": t.quality_score or 0,
            "isOpenSource": bool(t.is_open_source),
            "githubUrl": t.github_url,
            "categories": [c.slug for c in t.categories][:4],
        }
        for t in publishable
    ]
    payload = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "count": len(tools),
        "tools": tools,
    }
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {_OUT} ({len(tools)} publishable, dropped {dropped} as not public-ready).")


if __name__ == "__main__":
    main()
