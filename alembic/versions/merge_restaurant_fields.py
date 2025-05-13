"""merge restaurant fields

Revision ID: merge_restaurant_fields
Revises: 29b2c6823a4e, a56e4f8932bf
Create Date: 2023-05-19 15:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_restaurant_fields'
down_revision = ('29b2c6823a4e', 'a56e4f8932bf')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass 