"""Wholesale merchants and delivery sheets.

Revision ID: add_b_merchants
Revises: add_variant_stock_limits
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = 'add_b_merchants'
down_revision = 'add_variant_stock_limits'
branch_labels = None
depends_on = None


def _json():
    bind = op.get_bind()
    return mysql.JSON() if bind.dialect.name == 'mysql' else sa.JSON()


def upgrade():
    op.create_table(
        'b_merchants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('contact_person', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('show_prices', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('payment_terms', sa.Text(), nullable=False),
        sa.Column('payment_due_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_b_merchants_name', 'b_merchants', ['name'])

    op.create_table(
        'b_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('merchant_id', sa.Integer(), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('payment_terms', sa.Text(), nullable=False),
        sa.Column('show_prices', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('hst', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('discount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('grand_total', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default=sa.text("'unpaid'")),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('signature_images', _json(), nullable=True),
        sa.Column('check_images', _json(), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['b_merchants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_b_deliveries_merchant_id', 'b_deliveries', ['merchant_id'])
    op.create_index('ix_b_deliveries_invoice_date', 'b_deliveries', ['invoice_date'])
    op.create_index('ix_b_deliveries_payment_status', 'b_deliveries', ['payment_status'])

    op.create_table(
        'b_delivery_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('delivery_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Numeric(10, 2), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False, server_default=sa.text("'pc'")),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['delivery_id'], ['b_deliveries.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_b_delivery_lines_delivery_id', 'b_delivery_lines', ['delivery_id'])
    op.create_index('ix_b_delivery_lines_product_id', 'b_delivery_lines', ['product_id'])


def downgrade():
    op.drop_index('ix_b_delivery_lines_product_id', table_name='b_delivery_lines')
    op.drop_index('ix_b_delivery_lines_delivery_id', table_name='b_delivery_lines')
    op.drop_table('b_delivery_lines')
    op.drop_index('ix_b_deliveries_payment_status', table_name='b_deliveries')
    op.drop_index('ix_b_deliveries_invoice_date', table_name='b_deliveries')
    op.drop_index('ix_b_deliveries_merchant_id', table_name='b_deliveries')
    op.drop_table('b_deliveries')
    op.drop_index('ix_b_merchants_name', table_name='b_merchants')
    op.drop_table('b_merchants')
