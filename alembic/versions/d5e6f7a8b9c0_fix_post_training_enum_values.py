"""fix_post_training_enum_values

Fixes posttrainingnotificationstatus enum values from lowercase to uppercase
to match SQLAlchemy Enum behavior (uses .name, not .value).

This mismatch caused:
1. INSERT/SELECT failures with "invalid input value for enum"
2. Notifications sent but not recorded -> spam loop on every check cycle

Revision ID: d5e6f7a8b9c0
Revises: 4ee6fec1b520
Create Date: 2026-02-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = '4ee6fec1b520'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename enum values from lowercase to uppercase."""
    # Rename each enum value to match SQLAlchemy's Enum(.name) convention
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'sent' TO 'SENT'")
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'link_submitted' TO 'LINK_SUBMITTED'")
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'not_attended' TO 'NOT_ATTENDED'")
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'reminder_sent' TO 'REMINDER_SENT'")


def downgrade() -> None:
    """Rename enum values back to lowercase."""
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'SENT' TO 'sent'")
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'LINK_SUBMITTED' TO 'link_submitted'")
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'NOT_ATTENDED' TO 'not_attended'")
    op.execute("ALTER TYPE posttrainingnotificationstatus RENAME VALUE 'REMINDER_SENT' TO 'reminder_sent'")
