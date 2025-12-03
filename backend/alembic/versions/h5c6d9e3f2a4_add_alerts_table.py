"""add_alerts_table

Revision ID: h5c6d9e3f2a4
Revises: a978d460e6cf
Create Date: 2025-12-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h5c6d9e3f2a4'
down_revision: Union[str, Sequence[str], None] = 'a978d460e6cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types for alert_type and severity
    alerttype = postgresql.ENUM('stay-deviation', 'social-risk', name='alerttype', create_type=True)
    alerttype.create(op.get_bind(), checkfirst=True)
    
    alertseverity = postgresql.ENUM('low', 'medium', 'high', 'unknown', name='alertseverity', create_type=True)
    alertseverity.create(op.get_bind(), checkfirst=True)
    
    # Create alerts table
    op.create_table('alerts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('episode_id', sa.UUID(), nullable=False),
        sa.Column('alert_type', postgresql.ENUM('stay-deviation', 'social-risk', name='alerttype', create_type=False), nullable=False),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'unknown', name='alertseverity', create_type=False), nullable=False),
        sa.Column('message', sa.String(length=1000), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_alerts_episode_id',
        'alerts',
        'clinical_episodes',
        ['episode_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes for better query performance
    op.create_index(
        op.f('ix_alerts_episode_id'),
        'alerts',
        ['episode_id'],
        unique=False
    )
    
    op.create_index(
        op.f('ix_alerts_is_active'),
        'alerts',
        ['is_active'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_alerts_is_active'), table_name='alerts')
    op.drop_index(op.f('ix_alerts_episode_id'), table_name='alerts')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_alerts_episode_id', 'alerts', type_='foreignkey')
    
    # Drop alerts table
    op.drop_table('alerts')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS alerttype')
    op.execute('DROP TYPE IF EXISTS alertseverity')

