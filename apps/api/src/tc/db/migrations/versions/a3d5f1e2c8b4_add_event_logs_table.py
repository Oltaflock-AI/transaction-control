"""add event_logs table

Revision ID: a3d5f1e2c8b4
Revises: 1087cb75961c
Create Date: 2026-02-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d5f1e2c8b4'
down_revision: Union[str, None] = '1087cb75961c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('event_logs',
    sa.Column('transaction_id', sa.Uuid(), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=True),
    sa.Column('detail', sa.Text(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_logs_event_type'), 'event_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_event_logs_transaction_id'), 'event_logs', ['transaction_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_event_logs_transaction_id'), table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_event_type'), table_name='event_logs')
    op.drop_table('event_logs')
