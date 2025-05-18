"""manual_create_promo_codes_table

Revision ID: 326ad2c99882
Revises: 475a248d9153
Create Date: 2025-05-16 17:22:12.481317

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '326ad2c99882'
down_revision = '475a248d9153'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('promo_codes',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(), nullable=True, unique=True, index=True),
        sa.Column('discount_percent', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_to', sa.DateTime(), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('restaurant_id', sa.String(), sa.ForeignKey('restaurants.restaurant_id'), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now())
    )
    # Explicitly create index if not implicitly created by unique=True, though it often is.
    # op.create_index(op.f('ix_promo_codes_code'), 'promo_codes', ['code'], unique=True)
    # op.create_index(op.f('ix_promo_codes_id'), 'promo_codes', ['id'], unique=False) # Primary key is indexed by default


def downgrade():
    op.drop_table('promo_codes')
