"""add_grd_name_to_clinical_episode

Revision ID: a5b6c7d8e9f0
Revises: 178a1c94d141
Create Date: 2025-12-02 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5b6c7d8e9f0'
down_revision: Union[str, Sequence[str], None] = '178a1c94d141'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add grd_name column to clinical_episodes table
    op.add_column('clinical_episodes',
                  sa.Column('grd_name', sa.String(length=500), nullable=True,
                           comment='GRD diagnosis name (e.g., PH TRASPLANTE CARDÍACO Y/O PULMONAR W/MCC)'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove grd_name column
    op.drop_column('clinical_episodes', 'grd_name')
