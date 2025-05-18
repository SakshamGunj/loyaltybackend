"""add_restaurant_id_fk_to_users

Revision ID: 59a0b9621bf7
Revises: 07df425e12d8
Create Date: 2025-05-16 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59a0b9621bf7'
down_revision = '07df425e12d8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('restaurant_id', sa.String(), nullable=True))
        batch_op.create_index('ix_users_restaurant_id', ['restaurant_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_users_restaurant_id',
            'restaurants',
            ['restaurant_id'], ['restaurant_id']
        )

def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_restaurant_id', type_='foreignkey')
        batch_op.drop_index('ix_users_restaurant_id')
        batch_op.drop_column('restaurant_id')
