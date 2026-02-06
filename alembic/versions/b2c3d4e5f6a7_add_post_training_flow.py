"""add_post_training_flow

Adds training link fields to participations and creates post_training_notifications table.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add training link fields to participations
    op.add_column('participations', sa.Column('training_link', sa.String(length=500), nullable=True))
    op.add_column('participations', sa.Column('training_link_source', sa.String(length=20), nullable=True))
    op.add_column('participations', sa.Column('strava_activity_id', sa.BigInteger(), nullable=True))
    op.add_column('participations', sa.Column('strava_activity_data', sa.Text(), nullable=True))

    # Create post_training_notifications table
    op.create_table('post_training_notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('activity_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.Enum('sent', 'link_submitted', 'not_attended', 'reminder_sent', name='posttrainingnotificationstatus'), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('reminder_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_training_notifications_activity_id'), 'post_training_notifications', ['activity_id'], unique=False)
    op.create_index(op.f('ix_post_training_notifications_user_id'), 'post_training_notifications', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop post_training_notifications table
    op.drop_index(op.f('ix_post_training_notifications_user_id'), table_name='post_training_notifications')
    op.drop_index(op.f('ix_post_training_notifications_activity_id'), table_name='post_training_notifications')
    op.drop_table('post_training_notifications')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS posttrainingnotificationstatus')

    # Remove training link fields from participations
    op.drop_column('participations', 'strava_activity_data')
    op.drop_column('participations', 'strava_activity_id')
    op.drop_column('participations', 'training_link_source')
    op.drop_column('participations', 'training_link')
