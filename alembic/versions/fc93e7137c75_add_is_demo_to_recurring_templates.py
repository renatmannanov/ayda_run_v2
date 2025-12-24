"""add_is_demo_to_recurring_templates

Revision ID: fc93e7137c75
Revises: 0589ae247848
Create Date: 2025-12-24 17:52:55.830183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc93e7137c75'
down_revision: Union[str, Sequence[str], None] = '0589ae247848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_demo flag to recurring_templates table."""
    op.add_column('recurring_templates', sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='0'))
    op.create_index(op.f('ix_recurring_templates_is_demo'), 'recurring_templates', ['is_demo'], unique=False)


def downgrade() -> None:
    """Remove is_demo flag from recurring_templates table."""
    op.drop_index(op.f('ix_recurring_templates_is_demo'), table_name='recurring_templates')
    op.drop_column('recurring_templates', 'is_demo')
