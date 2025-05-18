"""\change_restaurant_id_to_string\

Revision ID: c4e7bcfe5ea6
Revises: f04463b3c33a
Create Date: 2025-05-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e7bcfe5ea6'
down_revision = 'f04463b3c33a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('restaurants', schema=None) as batch_op:
        # Step 1: Create a temporary table with the correct schema
        batch_op.execute('CREATE TABLE restaurants_new ('
                         'restaurant_id TEXT NOT NULL PRIMARY KEY, '
                         'restaurant_name TEXT, '
                         'offers TEXT, ' # Assuming JSON columns are stored as TEXT in SQLite
                         'points_per_rupee REAL, '
                         'points_per_spin REAL, '
                         'reward_thresholds TEXT, '
                         'spend_thresholds TEXT, '
                         'referral_rewards TEXT, '
                         'owner_uid TEXT, '
                         'admin_uid TEXT, '
                         'created_at TIMESTAMP, '
                         'FOREIGN KEY(owner_uid) REFERENCES users (uid))')

        # Step 2: Copy data from the old table to the new table
        # IMPORTANT: Column names must match what's in restaurants_old (which is current restaurants table)
        # The old table has restaurant_id as INTEGER, but it will be cast to TEXT if possible by SQLite.
        # If restaurant_id values are not purely numeric, this copy might fail for those rows.
        # However, since the error was 'baba' into INTEGER, existing data might be numeric or this is a new table.
        # For safety, we assume existing restaurant_id values are compatible with TEXT conversion.
        batch_op.execute('INSERT INTO restaurants_new (restaurant_id, restaurant_name, offers, points_per_rupee, points_per_spin, reward_thresholds, spend_thresholds, referral_rewards, owner_uid, admin_uid, created_at) '
                         'SELECT CAST(restaurant_id AS TEXT), restaurant_name, offers, points_per_rupee, points_per_spin, reward_thresholds, spend_thresholds, referral_rewards, owner_uid, admin_uid, created_at '
                         'FROM restaurants')

        # Step 3: Drop the old table
        batch_op.execute('DROP TABLE restaurants')

        # Step 4: Rename the new table to the original name
        batch_op.execute('ALTER TABLE restaurants_new RENAME TO restaurants')

        # Step 5: Recreate indexes if they were not part of CREATE TABLE (SQLite primary key implies index)
        # batch_op.create_index(batch_op.f('ix_restaurants_restaurant_name'), 'restaurants', ['restaurant_name'], unique=False)
        # restaurant_id is primary key, so it's indexed. owner_uid FK constraint does not imply index on its own in all DBs, but not critical here.


def downgrade():
    # This downgrade is complex because we'd have to convert TEXT back to INTEGER for restaurant_id.
    # If there are non-integer restaurant_ids, this would fail.
    # For simplicity in a development environment, a full reversal might not always be provided,
    # or it would require careful handling of data that can't be converted.
    
    with op.batch_alter_table('restaurants', schema=None) as batch_op:
        batch_op.execute('CREATE TABLE restaurants_old ('
                         'restaurant_id INTEGER NOT NULL PRIMARY KEY, ' # Reverting to INTEGER
                         'restaurant_name TEXT, '
                         'offers TEXT, '
                         'points_per_rupee REAL, '
                         'points_per_spin REAL, '
                         'reward_thresholds TEXT, '
                         'spend_thresholds TEXT, '
                         'referral_rewards TEXT, '
                         'owner_uid TEXT, '
                         'admin_uid TEXT, '
                         'created_at TIMESTAMP, '
                         'FOREIGN KEY(owner_uid) REFERENCES users (uid))')

        # Attempt to copy data, casting restaurant_id to INTEGER. This will fail if non-integer IDs exist.
        batch_op.execute('INSERT INTO restaurants_old (restaurant_id, restaurant_name, offers, points_per_rupee, points_per_spin, reward_thresholds, spend_thresholds, referral_rewards, owner_uid, admin_uid, created_at) '
                         'SELECT CAST(restaurant_id AS INTEGER), restaurant_name, offers, points_per_rupee, points_per_spin, reward_thresholds, spend_thresholds, referral_rewards, owner_uid, admin_uid, created_at '
                         'FROM restaurants')
        
        batch_op.execute('DROP TABLE restaurants')
        batch_op.execute('ALTER TABLE restaurants_old RENAME TO restaurants')
        
        # Recreate indexes if needed
        # batch_op.create_index(batch_op.f('ix_restaurants_restaurant_name'), 'restaurants', ['restaurant_name'], unique=False)

# Note: For JSON columns, SQLAlchemy handles the serialization/deserialization. 
# In SQLite, these are typically stored as TEXT. Using sa.JSON in op.create_table via Alembic ops is usually better.
# The raw SQL used here is for batch_alter_table context, which might behave differently.
# A more robust Alembic way for the upgrade would be:
# op.rename_table('restaurants', 'restaurants_old')
# op.create_table('restaurants',
#    sa.Column('restaurant_id', sa.String(), nullable=False, primary_key=True),
#    sa.Column('restaurant_name', sa.String(), index=True),
#    sa.Column('offers', sa.JSON()),
#    sa.Column('points_per_rupee', sa.Float()),
#    sa.Column('points_per_spin', sa.Float(), server_default='1.0'),
#    sa.Column('reward_thresholds', sa.JSON()),
#    sa.Column('spend_thresholds', sa.JSON()),
#    sa.Column('referral_rewards', sa.JSON()),
#    sa.Column('owner_uid', sa.String(), sa.ForeignKey('users.uid')),
#    sa.Column('admin_uid', sa.String(), nullable=True),
#    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
# )
# op.execute('INSERT INTO restaurants (...) SELECT CAST(restaurant_id AS TEXT), ... FROM restaurants_old')
# op.drop_table('restaurants_old')
# This alternative structure using op.create_table with SQLAlchemy types is generally preferred.
