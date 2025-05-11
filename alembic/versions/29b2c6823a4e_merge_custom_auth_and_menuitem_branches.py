"""merge custom auth and menuitem branches

Revision ID: 29b2c6823a4e
Revises: add_custom_auth_fields, f7409b44c3d2
Create Date: 2025-05-11 09:06:39.055571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29b2c6823a4e'
down_revision = ('add_custom_auth_fields', 'f7409b44c3d2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
