"""add invoice model

Revision ID: add_invoice_model
Revises: add_user_settings
Create Date: 2025-01-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import UUID

# revision identifiers, used by Alembic.
revision = 'add_invoice_model'
down_revision = 'add_user_settings'
branch_labels = Union[str, Sequence[str], None]
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create invoices table."""
    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('organization_id', UUID(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_invoice_id', sa.String(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', sa.Enum('draft', 'open', 'paid', 'void', 'uncollectible', name='invoice_status'), nullable=False, server_default='open'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invoice_pdf', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),

        # Indexes
        sa.PrimaryKeyConstraint('id', name='invoices_pkey'),
    )

    # Create indexes for faster lookups
    op.create_index('ix_invoices_organization_id', 'invoices', ['organization_id'])
    op.create_index('ix_invoices_stripe_invoice_id', 'invoices', ['stripe_invoice_id'])
    op.create_index('ix_invoices_status', 'invoices', ['status'])
    op.create_index('ix_invoices_deleted_at', 'invoices', ['deleted_at'])


def downgrade() -> None:
    """Drop invoices table."""
    op.drop_index('ix_invoices_deleted_at', table_name='invoices')
    op.drop_index('ix_invoices_status', table_name='invoices')
    op.drop_index('ix_invoices_stripe_invoice_id', table_name='invoices')
    op.drop_index('ix_invoices_organization_id', table_name='invoices')
    op.drop_table('invoices')

    # Drop the enum type
    op.execute('DROP TYPE IF EXISTS invoice_status')
