"""add_location_fields

Revision ID: a1b2c3d4e5f6
Revises: fc93e7137c75
Create Date: 2025-12-24 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fc93e7137c75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add location fields (country, city) to activities, clubs, groups, users."""
    # Activities
    op.add_column('activities', sa.Column('country', sa.String(length=100), nullable=False, server_default='Казахстан'))
    op.add_column('activities', sa.Column('city', sa.String(length=100), nullable=False, server_default='Алматы'))
    op.add_column('activities', sa.Column('recurring_sequence', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_activities_city'), 'activities', ['city'], unique=False)

    # Clubs
    op.add_column('clubs', sa.Column('country', sa.String(length=100), nullable=False, server_default='Казахстан'))
    op.add_column('clubs', sa.Column('city', sa.String(length=100), nullable=False, server_default='Алматы'))
    op.create_index(op.f('ix_clubs_city'), 'clubs', ['city'], unique=False)

    # Groups
    op.add_column('groups', sa.Column('country', sa.String(length=100), nullable=False, server_default='Казахстан'))
    op.add_column('groups', sa.Column('city', sa.String(length=100), nullable=False, server_default='Алматы'))
    op.create_index(op.f('ix_groups_city'), 'groups', ['city'], unique=False)

    # Users
    op.add_column('users', sa.Column('country', sa.String(length=100), nullable=False, server_default='Казахстан'))
    op.add_column('users', sa.Column('city', sa.String(length=100), nullable=False, server_default='Алматы'))
    op.create_index(op.f('ix_users_city'), 'users', ['city'], unique=False)


def downgrade() -> None:
    """Remove location fields."""
    # Users
    op.drop_index(op.f('ix_users_city'), table_name='users')
    op.drop_column('users', 'city')
    op.drop_column('users', 'country')

    # Groups
    op.drop_index(op.f('ix_groups_city'), table_name='groups')
    op.drop_column('groups', 'city')
    op.drop_column('groups', 'country')

    # Clubs
    op.drop_index(op.f('ix_clubs_city'), table_name='clubs')
    op.drop_column('clubs', 'city')
    op.drop_column('clubs', 'country')

    # Activities
    op.drop_index(op.f('ix_activities_city'), table_name='activities')
    op.drop_column('activities', 'recurring_sequence')
    op.drop_column('activities', 'city')
    op.drop_column('activities', 'country')
