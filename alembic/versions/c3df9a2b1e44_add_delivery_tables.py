"""add delivery tables (users, user_preferences, digest_log)

Revision ID: c3df9a2b1e44
Revises: b2ca612e0f01
Create Date: 2026-06-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3df9a2b1e44'
down_revision: Union[str, None] = 'b2ca612e0f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_table(
        'user_preferences',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('include_categories', sa.JSON(), nullable=False),
        sa.Column('exclude_categories', sa.JSON(), nullable=False),
        sa.Column('include_countries', sa.JSON(), nullable=False),
        sa.Column('exclude_countries', sa.JSON(), nullable=False),
        sa.Column('pricing_allow', sa.JSON(), nullable=False),
        sa.Column('min_quality_score', sa.Integer(), nullable=False),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('digest_cron', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )
    op.create_table(
        'digest_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('tool_ids', sa.JSON(), nullable=False),
        sa.Column('sent_on', sa.Date(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('delivery_status', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'channel', 'sent_on', name='uq_digest_log_user_channel_day'),
    )


def downgrade() -> None:
    op.drop_table('digest_log')
    op.drop_table('user_preferences')
    op.drop_table('users')
