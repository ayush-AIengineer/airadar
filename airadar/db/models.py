"""SQLAlchemy 2.0 models for AIRadar.

Maps the core tables from Architecture §7. Types are chosen to be **Postgres-faithful
but SQLite-runnable** so the Phase 1 walking skeleton runs on local SQLite and swaps to
Postgres in Phase 2 with no model changes:

- ``Uuid``            → native ``uuid`` on PG, ``CHAR(32)`` on SQLite
- ``DateTime(tz)``    → ``timestamptz`` on PG, ISO text on SQLite
- ``JSON``            → ``jsonb`` on PG (via variant), ``json`` text on SQLite

The Delivery stage tables (users, user_preferences, digest_log) live at the bottom of
this file (R5 / Architecture §4.5, §7).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Use JSONB on Postgres, plain JSON elsewhere (SQLite). Falls back automatically.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Source(Base):
    """Source registry — one row per data source, mapped to an adapter class."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    adapter_class: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[str] = mapped_column(String(1), nullable=False)  # 'A' | 'B' | 'C'
    config_jsonb: Mapped[dict[str, object]] = mapped_column(
        JSONType, nullable=False, default=dict
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str | None] = mapped_column(String)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    __table_args__ = (CheckConstraint("tier in ('A','B','C')", name="ck_sources_tier"),)


class CandidateURL(Base):
    """Raw discovery output — a URL that *might* describe a new AI tool."""

    __tablename__ = "candidate_urls"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sources.id"))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String, nullable=False)  # SHA256, fast lookup
    raw_title: Mapped[str | None] = mapped_column(Text)
    raw_excerpt: Mapped[str | None] = mapped_column(Text)
    signal_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_candidate_urls_url_hash"),
        Index("ix_candidate_urls_status_discovered", "status", "discovered_at"),
    )


class RawPage(Base):
    """Scraped, cleaned page text + screenshot reference."""

    __tablename__ = "raw_pages"

    id: Mapped[uuid.UUID] = _uuid_pk()
    candidate_url_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_urls.id"), unique=True
    )
    clean_text: Mapped[str | None] = mapped_column(Text)
    html_hash: Mapped[str | None] = mapped_column(String)
    screenshot_url: Mapped[str | None] = mapped_column(Text)
    fetcher_used: Mapped[str | None] = mapped_column(String)  # crawl4ai|playwright|trafilatura
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    word_count: Mapped[int | None] = mapped_column(Integer)
    # status: ok | low_quality | duplicate_html | error
    status: Mapped[str] = mapped_column(String, nullable=False)


class Tool(Base):
    """Canonical tool record — the single truth row for a tool."""

    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url_hash: Mapped[str] = mapped_column(String, nullable=False)
    one_liner: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    pricing_model: Mapped[str | None] = mapped_column(String)
    starting_price_usd_monthly: Mapped[float | None] = mapped_column(Numeric(10, 2))
    country_hq: Mapped[str | None] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    launch_date: Mapped[date | None] = mapped_column(DateTime(timezone=False))
    is_open_source: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    github_url: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    quality_score: Mapped[int | None] = mapped_column(Integer)  # 0–100
    is_duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tools.id"))
    # Curator/Dedup audit (Architecture §4.4): why this tool was kept/collapsed/scored.
    decision_reason: Mapped[str | None] = mapped_column(Text)
    curated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    categories: Mapped[list[Category]] = relationship(
        secondary="tool_categories", back_populates="tools"
    )
    evidence: Mapped[list[ToolEvidence]] = relationship(
        back_populates="tool", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("canonical_url_hash", name="uq_tools_canonical_url_hash"),
        Index("ix_tools_first_seen", "first_seen_at"),
        Index("ix_tools_quality", "quality_score"),
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)

    tools: Mapped[list[Tool]] = relationship(
        secondary="tool_categories", back_populates="categories"
    )


class ToolCategory(Base):
    __tablename__ = "tool_categories"

    tool_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), primary_key=True
    )


class ToolEvidence(Base):
    """Evidence trail — verbatim quote justifying each enriched field (anti-hallucination)."""

    __tablename__ = "tool_evidence"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tool_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tools.id", ondelete="CASCADE"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_quote: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    tool: Mapped[Tool] = relationship(back_populates="evidence")


class PipelineRun(Base):
    """Observability — one row per pipeline stage execution."""

    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stage: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(String, nullable=False)
    items_in: Mapped[int | None] = mapped_column(Integer)
    items_out: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 4))


# ── Delivery stage (Architecture §4.5, §7) ───────────────────────────────────
#
# Deviations from §7, made deliberately for the SQLite walking skeleton (swap-safe to
# Postgres in Phase 2 — see R0/R16 standard on documented deviations):
#   • List columns use JSONType (json on SQLite / jsonb on PG) instead of native PG
#     arrays, matching how ``Source.config_jsonb`` is already handled here.
#   • Category preferences are keyed by category *slug* (consistent with how enrichment
#     and the curator address categories), not the INT[] category ids in §7.
#   • Idempotency uses a dedicated ``sent_on`` Date column + unique constraint rather
#     than a ``DATE(sent_at)`` functional index — portable across SQLite and Postgres.


class User(Base):
    """A subscriber who receives personalized digests."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="UTC")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    preferences: Mapped[UserPreference | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)


class UserPreference(Base):
    """Per-user delivery filters and channels (Architecture §4.5)."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    include_categories: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )
    exclude_categories: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )
    include_countries: Mapped[list[str]] = mapped_column(  # ISO 3166-1 alpha-2
        JSONType, nullable=False, default=list
    )
    exclude_countries: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=list
    )
    pricing_allow: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)
    min_quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    channels: Mapped[list[str]] = mapped_column(
        JSONType, nullable=False, default=lambda: ["email"]
    )
    digest_cron: Mapped[str] = mapped_column(String, nullable=False, default="0 8 * * *")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="preferences")


class DigestLog(Base):
    """Delivery audit + idempotency record — one row per user/channel/day."""

    __tablename__ = "digest_log"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String, nullable=False)
    tool_ids: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)
    sent_on: Mapped[date] = mapped_column(Date, nullable=False)  # calendar day, for idempotency
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    delivery_status: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "channel", "sent_on", name="uq_digest_log_user_channel_day"
        ),
    )
