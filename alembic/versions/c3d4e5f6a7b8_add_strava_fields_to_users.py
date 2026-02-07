"""add_strava_fields_to_users

Adds Strava OAuth integration fields to users table:
- strava_athlete_id: Strava athlete ID (unique)
- strava_access_token: Encrypted OAuth access token
- strava_refresh_token: Encrypted OAuth refresh token
- strava_token_expires_at: Token expiration timestamp

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Strava fields to users table."""
    op.add_column('users', sa.Column('strava_athlete_id', sa.BigInteger(), nullable=True))
    op.add_column('users', sa.Column('strava_access_token', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('strava_refresh_token', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('strava_token_expires_at', sa.DateTime(), nullable=True))

    # Create unique index on strava_athlete_id
    op.create_index(
        op.f('ix_users_strava_athlete_id'),
        'users',
        ['strava_athlete_id'],
        unique=True
    )


def downgrade() -> None:
    """Remove Strava fields from users table."""
    op.drop_index(op.f('ix_users_strava_athlete_id'), table_name='users')
    op.drop_column('users', 'strava_token_expires_at')
    op.drop_column('users', 'strava_refresh_token')
    op.drop_column('users', 'strava_access_token')
    op.drop_column('users', 'strava_athlete_id')
