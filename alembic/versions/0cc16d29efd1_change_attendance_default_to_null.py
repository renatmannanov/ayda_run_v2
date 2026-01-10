"""change_attendance_default_to_null

Revision ID: 0cc16d29efd1
Revises: 5fe82fc8ee37
Create Date: 2026-01-10 15:29:58.593790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cc16d29efd1'
down_revision: Union[str, Sequence[str], None] = '5fe82fc8ee37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change default from False to NULL and update existing records
    # that have attended=False but status is not MISSED/ATTENDED (i.e., not marked yet)
    op.execute("""
        UPDATE participations
        SET attended = NULL
        WHERE attended = FALSE
        AND status NOT IN ('MISSED'::participationstatus, 'ATTENDED'::participationstatus)
    """)

    # Change column default to NULL
    op.alter_column('participations', 'attended',
                    server_default=None,
                    existing_type=sa.Boolean(),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Restore default to False
    op.alter_column('participations', 'attended',
                    server_default=sa.text('false'),
                    existing_type=sa.Boolean(),
                    existing_nullable=True)

    # Convert NULLs back to False
    op.execute("""
        UPDATE participations
        SET attended = FALSE
        WHERE attended IS NULL
    """)
