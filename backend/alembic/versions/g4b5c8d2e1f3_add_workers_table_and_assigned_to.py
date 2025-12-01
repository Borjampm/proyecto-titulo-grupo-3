"""add_workers_table_and_assigned_to

Revision ID: g4b5c8d2e1f3
Revises: f3a9c7e2d1b4
Create Date: 2025-12-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g4b5c8d2e1f3'
down_revision: Union[str, Sequence[str], None] = 'f3a9c7e2d1b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create workers table
    op.create_table('workers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Add assigned_to_id column to task_instances
    op.add_column('task_instances',
        sa.Column('assigned_to_id', sa.UUID(), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_task_instances_assigned_to_id',
        'task_instances',
        'workers',
        ['assigned_to_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for better query performance
    op.create_index(
        op.f('ix_task_instances_assigned_to_id'),
        'task_instances',
        ['assigned_to_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index(op.f('ix_task_instances_assigned_to_id'), table_name='task_instances')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_task_instances_assigned_to_id', 'task_instances', type_='foreignkey')
    
    # Drop assigned_to_id column
    op.drop_column('task_instances', 'assigned_to_id')
    
    # Drop workers table
    op.drop_table('workers')

