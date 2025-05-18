"""add_employee_fields_to_users_table (part 1: non-key columns)

Revision ID: 07df425e12d8
Revises: 7fec563f0c02
Create Date: 2025-05-16 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07df425e12d8'
down_revision = '7fec563f0c02'
branch_labels = None
depends_on = None


def upgrade():
    # Using raw SQL for adding columns to bypass potential batch mode issues
    op.execute("ALTER TABLE users ADD COLUMN designation VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN permissions JSON")
    # Note: SQLite stores JSON as TEXT. SQLAlchemy handles the type conversion.


def downgrade():
    # For downgrade, batch_alter_table is generally safer for dropping columns 
    # as it handles table recreation if needed (though less likely for simple drops).
    # However, to be consistent with raw SQL in upgrade for this specific issue, 
    # we might need to use raw SQL for drop if batch mode continues to be problematic.
    # For now, let's assume batch for downgrade is fine, as it's less complex than add + FK.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('permissions')
        batch_op.drop_column('designation')
