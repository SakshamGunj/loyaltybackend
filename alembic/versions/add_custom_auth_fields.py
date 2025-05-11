"""add custom auth fields

Revision ID: add_custom_auth_fields
Revises: bb8c1ff5c2eb
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_custom_auth_fields'
down_revision = 'bb8c1ff5c2eb'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    if 'number' not in columns:
        op.add_column('users', sa.Column('number', sa.String(), nullable=True))
    if 'hashed_password' not in columns:
        op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
    if 'role' not in columns:
        op.add_column('users', sa.Column('role', sa.String(), nullable=True, server_default='customer'))
    if 'created_at' not in columns:
        op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')))
    if 'is_active' not in columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    
    # Create indexes if they don't exist
    indexes = [i['name'] for i in inspector.get_indexes('users')]
    if 'ix_users_email' not in indexes:
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    if 'ix_users_number' not in indexes:
        op.create_index(op.f('ix_users_number'), 'users', ['number'], unique=True)
    if 'ix_users_uid' not in indexes:
        op.create_index(op.f('ix_users_uid'), 'users', ['uid'], unique=True)

def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    indexes = [i['name'] for i in inspector.get_indexes('users')]
    
    if 'ix_users_uid' in indexes:
        op.drop_index(op.f('ix_users_uid'), table_name='users')
    if 'ix_users_number' in indexes:
        op.drop_index(op.f('ix_users_number'), table_name='users')
    if 'ix_users_email' in indexes:
        op.drop_index(op.f('ix_users_email'), table_name='users')
    
    if 'is_active' in columns:
        op.drop_column('users', 'is_active')
    if 'created_at' in columns:
        op.drop_column('users', 'created_at')
    if 'role' in columns:
        op.drop_column('users', 'role')
    if 'hashed_password' in columns:
        op.drop_column('users', 'hashed_password')
    if 'number' in columns:
        op.drop_column('users', 'number') 