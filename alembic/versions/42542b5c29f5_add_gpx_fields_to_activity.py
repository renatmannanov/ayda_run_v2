"""add gpx fields to activity

Revision ID: 42542b5c29f5
Revises: 371b27fe8dfd
Create Date: 2025-12-22 12:38:17.782774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42542b5c29f5'
down_revision: Union[str, Sequence[str], None] = '371b27fe8dfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add GPX file fields to activities table
    op.add_column('activities', sa.Column('gpx_file_id', sa.String(length=255), nullable=True))
    op.add_column('activities', sa.Column('gpx_filename', sa.String(length=255), nullable=True))

    # Remove old gpx_file_channel_id (replaced by gpx_file_id)
    # Note: SQLite doesn't support DROP COLUMN in older versions
    # For SQLite, we skip this; for PostgreSQL it works fine
    try:
        op.drop_column('activities', 'gpx_file_channel_id')
    except Exception:
        pass  # SQLite may not support this


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add old column
    op.add_column('activities', sa.Column('gpx_file_channel_id', sa.INTEGER(), nullable=True))

    # Remove new GPX columns
    op.drop_column('activities', 'gpx_filename')
    op.drop_column('activities', 'gpx_file_id')
