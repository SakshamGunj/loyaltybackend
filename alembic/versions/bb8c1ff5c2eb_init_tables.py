"""init tables

Revision ID: bb8c1ff5c2eb
Revises: 
Create Date: 2025-04-18 22:19:05.360252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb8c1ff5c2eb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        uid VARCHAR NOT NULL, 
        name VARCHAR, 
        email VARCHAR, 
        created_at DATETIME, 
        PRIMARY KEY (uid)
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_uid ON users (uid)")

    op.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        restaurant_id INTEGER NOT NULL, 
        restaurant_name VARCHAR, 
        offers JSON, 
        points_per_rupee FLOAT, 
        reward_thresholds JSON, 
        referral_rewards JSON, 
        owner_uid VARCHAR, 
        created_at DATETIME, 
        PRIMARY KEY (restaurant_id), 
        FOREIGN KEY(owner_uid) REFERENCES users (uid)
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_restaurants_restaurant_id ON restaurants (restaurant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_restaurants_restaurant_name ON restaurants (restaurant_name)")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP TABLE IF EXISTS restaurants")
    op.execute("DROP TABLE IF EXISTS users")
    # ### end Alembic commands ###
