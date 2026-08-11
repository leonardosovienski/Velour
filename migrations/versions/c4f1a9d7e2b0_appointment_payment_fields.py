"""appointment payment fields

Revision ID: c4f1a9d7e2b0
Revises: b8d3db34366b
Create Date: 2026-08-11 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4f1a9d7e2b0'
down_revision: Union[str, Sequence[str], None] = 'b8d3db34366b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.add_column(sa.Column('paid', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('amount_paid', sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column(
            'payment_method',
            sa.Enum('cash', 'debit_card', 'credit_card', 'pix', 'other', name='paymentmethod'),
            nullable=True,
        ))
        batch_op.add_column(sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.alter_column('paid', server_default=None)
        batch_op.alter_column('reminder_sent', server_default=None)


def downgrade() -> None:
    with op.batch_alter_table('appointments') as batch_op:
        batch_op.drop_column('reminder_sent')
        batch_op.drop_column('payment_method')
        batch_op.drop_column('amount_paid')
        batch_op.drop_column('paid')
