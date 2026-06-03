"""Scrape orchestrator (Architecture §4.2).

Phase 1 ships the lightweight path: httpx fetch → trafilatura extraction. This is the
spec's tier-3 quality engine, used standalone here because it needs no browser download.
The Crawl4AI (tier-1) and Playwright (tier-2) fallbacks plug into :func:`fetch` in Phase 3
robustness work — the return contract stays identical.

Politeness (R2 / Architecture §12.4): identify the bot, respect a per-request timeout.
Full robots.txt + per-domain rate limiting lands with the Celery worker pool in Phase 3.
"""

from __future__ import annotations

import hashlib

import httpx
import trafilatura
from pydantic import BaseModel

USER_AGENT = "AIRadar-Bot/1.0 (+https://airadar.example/bot)"


class ScrapeResult(BaseModel):
    clean_text: str | None = None
    html_hash: str | None = None
    word_count: int = 0
    fetcher_used: str | None = None
    status: str  # ok | low_quality | error
    error: str | None = None


async def fetch(url: str, min_word_count: int = 100) -> ScrapeResult:
    """Fetch a URL and extract clean article text.

    Returns a ScrapeResult; never raises for network/extraction failures (records them
    as status='error' so the pipeline can continue on the next candidate).
    """
    try:
        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:  # noqa: BLE001 — fetch failures are recorded, not raised
        return ScrapeResult(status="error", fetcher_used="httpx", error=str(exc))

    html_hash = hashlib.sha256(html.encode("utf-8", "ignore")).hexdigest()
    clean_text = trafilatura.extract(html, include_comments=False, include_tables=False)

    if not clean_text:
        return ScrapeResult(
            status="low_quality",
            html_hash=html_hash,
            fetcher_used="trafilatura",
            word_count=0,
        )

    word_count = len(clean_text.split())
    status = "ok" if word_count >= min_word_count else "low_quality"
    return ScrapeResult(
        clean_text=clean_text,
        html_hash=html_hash,
        word_count=word_count,
        fetcher_used="trafilatura",
        status=status,
    )
