"""create_verified_phone_numbers_table

Revision ID: 5e9c6948cf81
Revises: c4e7bcfe5ea6
Create Date: 2025-05-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e9c6948cf81'
down_revision = 'c4e7bcfe5ea6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('verified_phone_numbers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.String(length=10), nullable=False),
        sa.Column('verified_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number', name='uq_verified_number')
    )
    op.create_index(op.f('ix_verified_phone_numbers_id'), 'verified_phone_numbers', ['id'], unique=False)
    op.create_index(op.f('ix_verified_phone_numbers_number'), 'verified_phone_numbers', ['number'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_verified_phone_numbers_number'), table_name='verified_phone_numbers')
    op.drop_index(op.f('ix_verified_phone_numbers_id'), table_name='verified_phone_numbers')
    op.drop_table('verified_phone_numbers')
