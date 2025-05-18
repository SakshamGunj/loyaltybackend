"""add_missing_fields_to_restaurants

Revision ID: f04463b3c33a
Revises: 3446abc02b28
Create Date: 2025-05-16 10:48:15.178114

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f04463b3c33a'
down_revision = '3446abc02b28'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('restaurants', sa.Column('points_per_spin', sa.Float(), nullable=True, server_default='1.0'))
    op.add_column('restaurants', sa.Column('spend_thresholds', sa.JSON(), nullable=True))
    op.add_column('restaurants', sa.Column('admin_uid', sa.String(), nullable=True))
    # Add a foreign key constraint for admin_uid if it references users.uid and if users table exists
    # For simplicity, assuming direct add; if FK is needed, it's usually op.create_foreign_key(...)
    # op.create_foreign_key('fk_restaurants_admin_uid', 'restaurants', 'users', ['admin_uid'], ['uid'])


def downgrade():
    # op.drop_constraint('fk_restaurants_admin_uid', 'restaurants', type_='foreignkey') # if FK was added
    op.drop_column('restaurants', 'admin_uid')
    op.drop_column('restaurants', 'spend_thresholds')
    op.drop_column('restaurants', 'points_per_spin')
