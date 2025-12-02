"""add_grd_norms_table

Revision ID: 178a1c94d141
Revises: g4b5c8d2e1f3
Create Date: 2025-12-02 14:37:29.644879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '178a1c94d141'
down_revision: Union[str, Sequence[str], None] = 'g4b5c8d2e1f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create grd_norms table
    op.create_table(
        'grd_norms',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('grd_id', sa.String(length=50), nullable=False, comment='GRD code identifier'),
        sa.Column('expected_days', sa.Integer(), nullable=False, comment='Expected stay days according to GRD norm (Est Media)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grd_id'),
    )

    # Create index on grd_id for fast lookups
    op.create_index(op.f('ix_grd_norms_grd_id'), 'grd_norms', ['grd_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index and table
    op.drop_index(op.f('ix_grd_norms_grd_id'), table_name='grd_norms')
    op.drop_table('grd_norms')
