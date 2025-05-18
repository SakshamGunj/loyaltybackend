"""merge_order_updates_with_main_restaurant_branch

Revision ID: 4f067dc2f3f8
Revises: 53611d32e43f, merge_restaurant_fields
Create Date: 2025-05-16 09:18:15.522674

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f067dc2f3f8'
down_revision = ('53611d32e43f', 'merge_restaurant_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
