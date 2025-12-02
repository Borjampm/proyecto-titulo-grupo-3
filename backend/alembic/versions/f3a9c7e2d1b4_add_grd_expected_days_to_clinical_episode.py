"""add_grd_expected_days_to_clinical_episode

Revision ID: f3a9c7e2d1b4
Revises: dcbdfe2fa8e2
Create Date: 2025-12-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a9c7e2d1b4'
down_revision: Union[str, Sequence[str], None] = 'dcbdfe2fa8e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add grd_expected_days column to store the expected stay days from GRD (Estancia Norma GRD)
    op.add_column('clinical_episodes',
                  sa.Column('grd_expected_days', sa.Integer(), nullable=True,
                           comment='Expected stay days from GRD (Estancia Norma GRD)'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove grd_expected_days column
    op.drop_column('clinical_episodes', 'grd_expected_days')


