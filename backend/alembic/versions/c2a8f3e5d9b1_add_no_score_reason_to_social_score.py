"""add_no_score_reason_to_social_score

Revision ID: c2a8f3e5d9b1
Revises: 0f72d9b4974b
Create Date: 2025-11-25 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a8f3e5d9b1'
down_revision: Union[str, Sequence[str], None] = '0f72d9b4974b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make score column nullable to support cases where score couldn't be calculated
    op.alter_column('social_score_history', 'score',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    # Add no_score_reason column to store the reason when score is null (from "Motivo" column)
    op.add_column('social_score_history',
                  sa.Column('no_score_reason', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove no_score_reason column
    op.drop_column('social_score_history', 'no_score_reason')
    
    # Make score column non-nullable again (note: this may fail if there are null scores)
    op.alter_column('social_score_history', 'score',
                    existing_type=sa.Integer(),
                    nullable=False)

