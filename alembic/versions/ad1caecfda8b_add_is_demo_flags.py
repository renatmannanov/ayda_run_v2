"""add_is_demo_flags

Revision ID: ad1caecfda8b
Revises: 15291782162b
Create Date: 2025-12-24 14:06:33.404822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad1caecfda8b'
down_revision: Union[str, Sequence[str], None] = '15291782162b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_demo flags to users, clubs, groups, and activities tables."""
    # Add is_demo to users
    op.add_column('users', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_users_is_demo'), 'users', ['is_demo'], unique=False)

    # Add is_demo to clubs
    op.add_column('clubs', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_clubs_is_demo'), 'clubs', ['is_demo'], unique=False)

    # Add is_demo to groups
    op.add_column('groups', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_groups_is_demo'), 'groups', ['is_demo'], unique=False)

    # Add is_demo to activities
    op.add_column('activities', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_activities_is_demo'), 'activities', ['is_demo'], unique=False)


def downgrade() -> None:
    """Remove is_demo flags from tables."""
    # Remove from activities
    op.drop_index(op.f('ix_activities_is_demo'), table_name='activities')
    op.drop_column('activities', 'is_demo')

    # Remove from groups
    op.drop_index(op.f('ix_groups_is_demo'), table_name='groups')
    op.drop_column('groups', 'is_demo')

    # Remove from clubs
    op.drop_index(op.f('ix_clubs_is_demo'), table_name='clubs')
    op.drop_column('clubs', 'is_demo')

    # Remove from users
    op.drop_index(op.f('ix_users_is_demo'), table_name='users')
    op.drop_column('users', 'is_demo')
