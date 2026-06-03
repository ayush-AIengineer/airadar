"""Single source of configuration for AIRadar.

Per the Project Architect role (R0): every cross-cutting setting flows through this
one `Settings` object, loaded from environment / `.env`. Nothing reads `os.environ`
directly elsewhere.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, populated from env vars prefixed with ``AIRADAR_``."""

    model_config = SettingsConfigDict(
        env_prefix="AIRADAR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Environment ──────────────────────────────────────────────────────────
    env: Literal["local", "staging", "prod"] = "local"

    # ── Database ─────────────────────────────────────────────────────────────
    # Phase 1 default is local SQLite (async). Postgres swaps in via env in Phase 2.
    database_url: str = "sqlite+aiosqlite:///./airadar.db"
    db_echo: bool = False

    # ── LLM ──────────────────────────────────────────────────────────────────
    anthropic_api_key: str = ""
    enrichment_model: str = "claude-sonnet-4-6"
    classifier_model: str = "claude-haiku-4-5-20251001"

    # ── Pipeline tuning (mirrors Architecture §11 cost discipline) ───────────
    discovery_signal_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    max_enrichment_per_day: int = Field(default=300, gt=0)
    min_word_count: int = Field(default=100, ge=0)

    # ── Source credentials ───────────────────────────────────────────────────
    producthunt_token: str = ""
    github_token: str = ""

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton settings object."""
    return Settings()
