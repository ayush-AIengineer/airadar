"""Repository for users and their delivery preferences (one aggregate per file — R6)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from airadar.db.models import User, UserPreference


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result: User | None = await session.scalar(
        select(User).where(User.email == email).options(selectinload(User.preferences))
    )
    return result


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    timezone: str = "UTC",
    include_categories: list[str] | None = None,
    pricing_allow: list[str] | None = None,
    min_quality_score: int = 30,
    channels: list[str] | None = None,
) -> User:
    """Create a user with a default preferences row. Caller ensures email is unique."""
    user = User(email=email, timezone=timezone)
    user.preferences = UserPreference(
        include_categories=include_categories or [],
        pricing_allow=pricing_allow or [],
        min_quality_score=min_quality_score,
        channels=channels or ["email"],
    )
    session.add(user)
    await session.flush()
    return user


async def list_subscribers(session: AsyncSession) -> list[User]:
    """All users with their preferences eager-loaded, for the Delivery agent."""
    result = await session.scalars(
        select(User).options(selectinload(User.preferences)).order_by(User.created_at)
    )
    return list(result)
