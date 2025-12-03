"""
Add overstay probability and GRD-related fields to clinical_episodes

Revision ID: e1a2b3c4d5e6
Revises: f3a9c7e2d1b4
Create Date: 2025-12-02
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'f3a9c7e2d1b4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('clinical_episodes', sa.Column('grd_id', sa.String(length=128), nullable=True))
    op.add_column('clinical_episodes', sa.Column('overstay_probability', sa.Float(), nullable=True))
    op.add_column('clinical_episodes', sa.Column('prevision_desc', sa.String(length=500), nullable=True))
    op.add_column('clinical_episodes', sa.Column('tipo_ingreso_desc', sa.String(length=500), nullable=True))
    op.add_column('clinical_episodes', sa.Column('servicio_ingreso_desc', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('clinical_episodes', 'servicio_ingreso_desc')
    op.drop_column('clinical_episodes', 'tipo_ingreso_desc')
    op.drop_column('clinical_episodes', 'peso_grd_medio_todos')
    op.drop_column('clinical_episodes', 'ir_tipo_grd')
    op.drop_column('clinical_episodes', 'prevision_desc')
    op.drop_column('clinical_episodes', 'overstay_probability')
    op.drop_column('clinical_episodes', 'grd_id')
