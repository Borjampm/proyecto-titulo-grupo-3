"""add server defaults to patients created_at and updated_at

Revision ID: a1e6596d27b1
Revises: b32340fbec94
Create Date: 2025-10-17 11:30:09.363983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1e6596d27b1'
down_revision: Union[str, Sequence[str], None] = 'b32340fbec94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add server defaults to created_at and updated_at columns
    op.alter_column('patients', 'created_at',
                    server_default=sa.text('now()'))
    op.alter_column('patients', 'updated_at',
                    server_default=sa.text('now()'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove server defaults from created_at and updated_at columns
    op.alter_column('patients', 'created_at',
                    server_default=None)
    op.alter_column('patients', 'updated_at',
                    server_default=None)
