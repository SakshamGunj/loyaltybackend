"""Add restaurant fields to Order

Revision ID: a56e4f8932bf
Revises: order_id_format_change
Create Date: 2023-05-19 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a56e4f8932bf'
down_revision = 'order_id_format_change'
branch_labels = None
depends_on = None


def upgrade():
    # Add the restaurant_id and restaurant_name columns to the orders table
    # These columns are now created by order_id_format_change.py, so these lines are redundant.
    # op.add_column('orders', sa.Column('restaurant_id', sa.String(), nullable=True))
    # op.add_column('orders', sa.Column('restaurant_name', sa.String(), nullable=True))
    pass # Intentionally doing nothing as parent migration now handles this.


def downgrade():
    # Remove the columns if needed - corresponding to the (now removed) add_column calls
    # If order_id_format_change.py is downgraded, it would remove the table or these columns anyway.
    # op.drop_column('orders', 'restaurant_name')
    # op.drop_column('orders', 'restaurant_id') 
    pass # Intentionally doing nothing. 