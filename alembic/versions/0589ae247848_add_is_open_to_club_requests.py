"""add_is_open_to_club_requests

Revision ID: 0589ae247848
Revises: ad1caecfda8b
Create Date: 2025-12-24 16:36:06.390310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0589ae247848'
down_revision: Union[str, Sequence[str], None] = 'ad1caecfda8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_open column to club_requests table."""
    op.add_column('club_requests', sa.Column('is_open', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    """Remove is_open column from club_requests table."""
    op.drop_column('club_requests', 'is_open')
