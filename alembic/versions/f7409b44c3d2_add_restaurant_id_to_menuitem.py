"""Add restaurant_id to MenuItem

Revision ID: f7409b44c3d2
Revises: 23a1f18eb6c5
Create Date: 2025-04-30 10:38:44.405781

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7409b44c3d2'
down_revision = '23a1f18eb6c5'
branch_labels = None
depends_on = None


def upgrade():
    # Drop leftover temp table if exists
    conn = op.get_bind()
    conn.execute("DROP TABLE IF EXISTS menu_categories_new")

    # --- Add restaurant_id to menu_items via table recreation (SQLite safe) ---
    # 1. Rename old table
    op.execute("ALTER TABLE menu_items RENAME TO menu_items_old")
    # 2. Create new table with restaurant_id, image_url, and created_at
    op.create_table(
        'menu_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('restaurant_id', sa.String, sa.ForeignKey('restaurants.restaurant_id'), index=True, nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.String, nullable=True),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('available', sa.Boolean, default=True, server_default='1'),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('menu_categories.id'), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True)
    )
    # 3. Copy data including image_url and created_at
    op.execute("INSERT INTO menu_items (id, restaurant_id, name, description, price, available, category_id, image_url, created_at) SELECT id, restaurant_id, name, description, price, available, category_id, image_url, created_at FROM menu_items_old")
    # 4. Drop old table
    op.execute("DROP TABLE menu_items_old")
    # 5. Drop index if exists (SQLite safety) - restaurant_id index is now created by create_table
    # 6. Create index - No longer needed explicitly if create_table handled it with index=True
    # 6. Create foreign key - (already set in create_table)
    # --- End SQLite-safe migration ---


def downgrade():
    # Downgrade should ideally recreate menu_items_old from the current menu_items,
    # then drop the current and rename. For simplicity, if this is dev:
    op.execute("ALTER TABLE menu_items RENAME TO menu_items_temp_for_downgrade")
    op.create_table(
        'menu_items', # This is now the schema *before* this migration's changes
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.String, nullable=True),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('available', sa.Boolean, default=True, server_default='1'),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('menu_categories.id'), nullable=True),
        sa.Column('image_url', sa.String(), nullable=True), # Keep image_url if it was there before this migration
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True) # Keep created_at
    )
    op.execute("INSERT INTO menu_items (id, name, description, price, available, category_id, image_url, created_at) SELECT id, name, description, price, available, category_id, image_url, created_at FROM menu_items_temp_for_downgrade")
    op.execute("DROP TABLE menu_items_temp_for_downgrade")
    # The original auto-generated downgrade was simpler:
    # op.drop_constraint(None, 'menu_items', type_='foreignkey') # For restaurant_id FK
    # op.drop_index(op.f('ix_menu_items_restaurant_id'), table_name='menu_items')
    # op.drop_column('menu_items', 'restaurant_id')
    # ... (other parts related to menu_categories from original auto-gen are likely fine)
