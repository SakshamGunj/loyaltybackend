"""Make restaurant_id NOT NULL in menu_categories

Revision ID: 23a1f18eb6c5
Revises: order_id_format_change
Create Date: 2025-04-28 11:58:46.089014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23a1f18eb6c5'
down_revision = 'order_id_format_change'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure no NULLs exist in restaurant_id
    from sqlalchemy import text
    conn = op.get_bind()
    # Check if menu_categories table exists before querying it
    table_exists = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_categories'")).scalar_one_or_none()
    if table_exists:
        null_count = conn.execute(text("SELECT COUNT(*) FROM menu_categories WHERE restaurant_id IS NULL")).scalar()
        if null_count > 0:
            raise Exception("Cannot make restaurant_id NOT NULL: NULL values exist in menu_categories. Please update or remove these rows before upgrading.")

    # Create new table with NOT NULL constraint and created_at
    op.execute('''
        CREATE TABLE menu_categories_new (
            id INTEGER PRIMARY KEY,
            restaurant_id VARCHAR NOT NULL REFERENCES restaurants (restaurant_id),
            name VARCHAR NOT NULL UNIQUE,
            description VARCHAR,
            created_at TIMESTAMP,  -- Added created_at
            CONSTRAINT uq_menu_categories_name UNIQUE (name)
        )
    ''')
    # Copy data including created_at. If created_at didn't exist in the old table (first run), it will be NULL.
    # The model has a default for created_at, so new inserts via app will be fine.
    # For existing data, if old table had created_at, it's copied. If not, it becomes NULL here, then model default applies for future app interactions.
    op.execute('''
        INSERT INTO menu_categories_new (id, restaurant_id, name, description, created_at)
        SELECT id, restaurant_id, name, description, created_at FROM menu_categories
    ''')
    op.execute('DROP TABLE menu_categories')
    op.execute('ALTER TABLE menu_categories_new RENAME TO menu_categories')
    op.create_index(op.f('ix_menu_categories_restaurant_id'), 'menu_categories', ['restaurant_id'], unique=False)
    # op.create_foreign_key(None, 'menu_categories', 'restaurants', ['restaurant_id'], ['restaurant_id']) # Removed redundant FK creation
    # ### end Alembic commands ###


def downgrade():
    # Recreate table without created_at and with nullable restaurant_id
    op.execute('''
        CREATE TABLE menu_categories_old (
            id INTEGER PRIMARY KEY,
            restaurant_id VARCHAR REFERENCES restaurants (restaurant_id),
            name VARCHAR NOT NULL UNIQUE,
            description VARCHAR,
            CONSTRAINT uq_menu_categories_name UNIQUE (name)
        )
    ''')
    op.execute('''
        INSERT INTO menu_categories_old (id, restaurant_id, name, description)
        SELECT id, restaurant_id, name, description FROM menu_categories
    ''')
    op.execute('DROP TABLE menu_categories')
    op.execute('ALTER TABLE menu_categories_old RENAME TO menu_categories')
    op.create_index(op.f('ix_menu_categories_restaurant_id'), 'menu_categories', ['restaurant_id'], unique=False)
    # ### end Alembic commands ###
