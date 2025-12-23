"""add show_photo to users

Revision ID: 15291782162b
Revises: 42542b5c29f5
Create Date: 2025-12-23 14:09:30.258230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15291782162b'
down_revision: Union[str, Sequence[str], None] = '42542b5c29f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add show_photo column with default True
    op.add_column('users', sa.Column('show_photo', sa.Boolean(), nullable=False, server_default='1'))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'show_photo')
    # ### end Alembic commands ###
