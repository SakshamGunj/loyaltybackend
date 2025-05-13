"""Change order ID format to restaurant-specific

Revision ID: order_id_format_change
Revises: merge_restaurant_fields
Create Date: 2023-05-20 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from sqlalchemy import Column, String, Integer, ForeignKey


# revision identifiers, used by Alembic.
revision = 'order_id_format_change'
down_revision = 'merge_restaurant_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new orders table with string ID
    op.create_table(
        'orders_new',
        sa.Column('id', sa.String(), primary_key=True, index=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('payment_status', sa.String(), nullable=True),
        sa.Column('promo_code_id', sa.Integer(), sa.ForeignKey('promo_codes.id'), nullable=True),
        sa.Column('restaurant_id', sa.String(), nullable=True),
        sa.Column('restaurant_name', sa.String(), nullable=True),
        sa.Column('order_number', sa.Integer(), nullable=True),
    )
    
    # Create new order_items table that references string order IDs
    op.create_table(
        'order_items_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('menu_items.id'), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
    )
    
    # Create new order_status_history table
    op.create_table(
        'order_status_history_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=True),
        sa.Column('changed_by', sa.String(), nullable=False),
    )
    
    # Create new payments table
    op.create_table(
        'payments_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('transaction_id', sa.String(), nullable=True),
    )
    
    # Create new audit_logs table
    op.create_table(
        'audit_logs_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.uid'), nullable=True),
        sa.Column('action', sa.String(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=True),
    )
    
    # Note: Data migration should be done through code after this migration runs
    # This is because SQLite doesn't support ALTER TABLE ... MODIFY COLUMN


def downgrade():
    # Drop the new tables in reverse order
    op.drop_table('audit_logs_new')
    op.drop_table('payments_new')
    op.drop_table('order_status_history_new')
    op.drop_table('order_items_new')
    op.drop_table('orders_new') 