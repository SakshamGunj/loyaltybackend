"""Add restaurant fields to Order

Revision ID: a56e4f8932bf
Revises: e4c3ec824012
Create Date: 2023-05-19 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a56e4f8932bf'
down_revision = 'e4c3ec824012'
branch_labels = None
depends_on = None


def upgrade():
    # Add the restaurant_id and restaurant_name columns to the orders table
    op.add_column('orders', sa.Column('restaurant_id', sa.String(), nullable=True))
    op.add_column('orders', sa.Column('restaurant_name', sa.String(), nullable=True))


def downgrade():
    # Remove the columns if needed
    op.drop_column('orders', 'restaurant_name')
    op.drop_column('orders', 'restaurant_id') 