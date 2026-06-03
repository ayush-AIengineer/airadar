"""Repository for canonical tool records, categories, and evidence."""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from airadar.db.models import Category as CategoryRow
from airadar.db.models import Tool, ToolEvidence


def canonical_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def exists_by_hash(session: AsyncSession, url_hash: str) -> bool:
    existing = await session.scalar(
        select(Tool.id).where(Tool.canonical_url_hash == url_hash)
    )
    return existing is not None


async def get_or_create_category(session: AsyncSession, slug: str) -> CategoryRow:
    row = await session.scalar(select(CategoryRow).where(CategoryRow.slug == slug))
    if row is None:
        row = CategoryRow(slug=slug, name=slug.replace("_", " ").title())
        session.add(row)
        await session.flush()
    return row


async def insert_tool(
    session: AsyncSession,
    *,
    name: str,
    canonical_url: str,
    one_liner: str | None,
    description: str | None,
    pricing_model: str,
    starting_price_usd_monthly: float | None,
    country_hq: str | None,
    launch_date: date | None,
    is_open_source: bool,
    github_url: str | None,
    confidence_score: float,
    category_slugs: list[str],
) -> Tool:
    tool = Tool(
        name=name,
        canonical_url=canonical_url,
        canonical_url_hash=canonical_hash(canonical_url),
        one_liner=one_liner,
        description=description,
        pricing_model=pricing_model,
        starting_price_usd_monthly=starting_price_usd_monthly,
        country_hq=country_hq,
        launch_date=launch_date,
        is_open_source=is_open_source,
        github_url=github_url,
        confidence_score=confidence_score,
    )
    session.add(tool)
    # Add to the session before linking categories so autoflush can persist the
    # association rows (avoids "Object of type <Tool> not in session" warnings).
    for slug in category_slugs:
        tool.categories.append(await get_or_create_category(session, slug))
    await session.flush()
    return tool


def add_evidence(
    session: AsyncSession,
    *,
    tool_id: uuid.UUID,
    field_name: str,
    field_value: str,
    evidence_quote: str,
    evidence_url: str,
    extracted_at: datetime,
) -> None:
    session.add(
        ToolEvidence(
            tool_id=tool_id,
            field_name=field_name,
            field_value=field_value,
            evidence_quote=evidence_quote,
            evidence_url=evidence_url,
            extracted_at=extracted_at,
        )
    )
