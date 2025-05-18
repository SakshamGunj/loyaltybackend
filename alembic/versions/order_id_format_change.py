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
down_revision = 'e4c3ec824012'
branch_labels = None
depends_on = None


def upgrade():
    # Step -1: Create PromoCode table as it's a dependency for orders_new table's FK
    op.create_table(
        'promo_codes',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('code', sa.String(), unique=True, index=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('discount_percent', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_to', sa.DateTime(), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('restaurant_id', sa.String(), sa.ForeignKey('restaurants.restaurant_id'), nullable=True), # Assuming FK to restaurants
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True)
    )

    # Step 0: Create MenuCategory and MenuItem tables first, as order_items_new will depend on menu_items
    op.create_table(
        'menu_categories',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('restaurant_id', sa.String(), sa.ForeignKey('restaurants.restaurant_id'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint('name', name='uq_menu_categories_name') # Model has unique=True on name
    )

    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('restaurant_id', sa.String(), sa.ForeignKey('restaurants.restaurant_id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('available', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('menu_categories.id'), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True)
    )

    # Step 1: Create all the new tables with '_new' suffix
    op.create_table(
        'orders_new',
        sa.Column('id', sa.String(), primary_key=True, index=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.uid'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('status', sa.String(), nullable=True, server_default='Pending'),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('payment_status', sa.String(), nullable=True, server_default='Pending'),
        sa.Column('promo_code_id', sa.Integer(), sa.ForeignKey('promo_codes.id'), nullable=True),
        sa.Column('restaurant_id', sa.String(), sa.ForeignKey('restaurants.restaurant_id'), nullable=True),
        sa.Column('restaurant_name', sa.String(), nullable=True),
        sa.Column('order_number', sa.Integer(), nullable=True),
    )
    
    op.create_table(
        'order_items_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=True),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('menu_items.id'), nullable=True),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=True),
    )
    
    op.create_table(
        'order_status_history_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('changed_by', sa.String(), nullable=False),
    )
    
    op.create_table(
        'payments_new',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('order_id', sa.String(), sa.ForeignKey('orders_new.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='Pending', nullable=True),
        sa.Column('processed_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('transaction_id', sa.String(), nullable=True),
    )

    # Step 2: Drop old tables (if they existed and this migration is replacing them)
    # For safety, wrap in try-except or check existence if Alembic/SQLite supports it easily
    # op.drop_table('audit_logs_old_if_any') # Example, adjust name
    # op.drop_table('payments_old_if_any')
    # op.drop_table('order_status_history_old_if_any')
    # op.drop_table('order_items_old_if_any')
    # op.drop_table('orders_old_if_any')
    # NOTE: Dropping tables that your models.py might still point to (if 'orders' __tablename__ was used)
    # before renaming is risky if not done in the right sequence or if old data needs migration.
    # For a fresh start (delete DB file), these drops are less critical but good for idempotent reruns.
    # Given this migration's purpose, it's likely replacing older versions of these tables.

    # Step 3: Rename new tables to their final names
    op.rename_table('orders_new', 'orders')
    op.rename_table('order_items_new', 'order_items')
    op.rename_table('order_status_history_new', 'order_status_history')
    op.rename_table('payments_new', 'payments')
    
    # Note: Data migration from old tables to new tables would typically happen
    # *before* dropping old tables and *before* renaming new tables,
    # often using op.execute(sa.text(...)) for raw SQL inserts/selects.
    # This script assumes either no old data or data migration handled elsewhere.

def downgrade():
    # Reverse of upgrade: rename back to '_new', then drop '_new' tables.
    # Recreating the *exact* old schema in downgrade can be complex.
    # Often, for dev, a simple drop is used if the DB is frequently reset.

    op.rename_table('payments', 'payments_new')
    op.rename_table('order_status_history', 'order_status_history_new')
    op.rename_table('order_items', 'order_items_new')
    op.rename_table('orders', 'orders_new')

    # Drop the '_new' (now renamed from final) tables
    op.drop_table('payments_new')
    op.drop_table('order_status_history_new')
    op.drop_table('order_items_new')
    op.drop_table('orders_new')
    
    # Drop MenuCategory and MenuItem tables (created in upgrade step 0)
    op.drop_table('menu_items')
    op.drop_table('menu_categories')

    # Drop PromoCode table (created in upgrade step -1)
    op.drop_table('promo_codes')
    
    # If you had truly old tables that were dropped in upgrade, you'd recreate their original old schema here.
    # e.g., op.create_table('orders_old_if_any', ...)
    # This part is omitted for brevity as the old schema isn't defined. 