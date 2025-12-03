"""merge alerts and overstay branches

Revision ID: i6d7e0f4a5b6
Revises: h5c6d9e3f2a4, e1a2b3c4d5e6
Create Date: 2025-12-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i6d7e0f4a5b6'
down_revision: Union[str, Sequence[str], None] = ('h5c6d9e3f2a4', 'e1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

