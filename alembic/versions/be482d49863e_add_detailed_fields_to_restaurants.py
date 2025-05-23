"""add_detailed_fields_to_restaurants

Revision ID: be482d49863e
Revises: c44d3bcb0e90
Create Date: 2025-05-16 14:33:52.075970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be482d49863e'
down_revision = 'c44d3bcb0e90'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('restaurants', sa.Column('address', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('contact_phone', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('email', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('tax_id', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('currency', sa.String(), nullable=False, server_default='INR'))
    op.add_column('restaurants', sa.Column('timezone', sa.String(), nullable=False, server_default='Asia/Kolkata'))
    op.add_column('restaurants', sa.Column('opening_time', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('closing_time', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('is_open', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('restaurants', sa.Column('weekly_off_days', sa.JSON(), nullable=True, server_default='[]')) # Default to empty JSON list
    op.add_column('restaurants', sa.Column('accepted_payment_modes', sa.JSON(), nullable=True, server_default='["Cash", "Card", "UPI"]')) # Default to JSON list
    op.add_column('restaurants', sa.Column('allow_manual_discount', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('restaurants', sa.Column('bill_number_prefix', sa.String(), nullable=True))
    op.add_column('restaurants', sa.Column('bill_series_start', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('restaurants', sa.Column('show_tax_breakdown_on_invoice', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('restaurants', sa.Column('enable_tips_collection', sa.Boolean(), nullable=False, server_default=sa.false()))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('restaurants', 'enable_tips_collection')
    op.drop_column('restaurants', 'show_tax_breakdown_on_invoice')
    op.drop_column('restaurants', 'bill_series_start')
    op.drop_column('restaurants', 'bill_number_prefix')
    op.drop_column('restaurants', 'allow_manual_discount')
    op.drop_column('restaurants', 'accepted_payment_modes')
    op.drop_column('restaurants', 'weekly_off_days')
    op.drop_column('restaurants', 'is_open')
    op.drop_column('restaurants', 'closing_time')
    op.drop_column('restaurants', 'opening_time')
    op.drop_column('restaurants', 'timezone')
    op.drop_column('restaurants', 'currency')
    op.drop_column('restaurants', 'tax_id')
    op.drop_column('restaurants', 'email')
    op.drop_column('restaurants', 'contact_phone')
    op.drop_column('restaurants', 'address')
    # ### end Alembic commands ###
