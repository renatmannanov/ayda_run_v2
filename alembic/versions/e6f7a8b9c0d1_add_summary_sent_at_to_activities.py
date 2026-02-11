"""add_summary_sent_at_to_activities

Adds summary_sent_at column to activities table to track whether
trainer summary was already sent. Prevents duplicate summaries on restart.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-02-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add summary_sent_at column."""
    op.add_column('activities', sa.Column('summary_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove summary_sent_at column."""
    op.drop_column('activities', 'summary_sent_at')
