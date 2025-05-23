BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> bb8c1ff5c2eb

CREATE TABLE IF NOT EXISTS users (
        uid VARCHAR NOT NULL, 
        name VARCHAR, 
        email VARCHAR, 
        created_at DATETIME, 
        PRIMARY KEY (uid)
    );

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique ON users (email);

CREATE INDEX IF NOT EXISTS ix_users_uid ON users (uid);

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
    );

CREATE INDEX IF NOT EXISTS ix_restaurants_restaurant_id ON restaurants (restaurant_id);

CREATE INDEX IF NOT EXISTS ix_restaurants_restaurant_name ON restaurants (restaurant_name);

INSERT INTO alembic_version (version_num) VALUES ('bb8c1ff5c2eb') RETURNING alembic_version.version_num;

-- Running upgrade bb8c1ff5c2eb -> 2e38b4c5d7c0

CREATE TABLE audit_logs (
    id SERIAL NOT NULL, 
    user_id VARCHAR, 
    action VARCHAR, 
    details JSON, 
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    order_id VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (uid), 
    FOREIGN KEY(order_id) REFERENCES orders (id)
);

CREATE INDEX ix_audit_logs_id ON audit_logs (id);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);

CREATE INDEX ix_audit_logs_order_id ON audit_logs (order_id);

CREATE TABLE claimed_rewards (
    id SERIAL NOT NULL, 
    uid VARCHAR, 
    restaurant_id VARCHAR, 
    reward_name VARCHAR, 
    threshold_id INTEGER, 
    whatsapp_number VARCHAR, 
    user_name VARCHAR, 
    claimed_at TIMESTAMP WITHOUT TIME ZONE, 
    redeemed BOOLEAN, 
    redeemed_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id), 
    FOREIGN KEY(uid) REFERENCES users (uid)
);

CREATE INDEX ix_claimed_rewards_id ON claimed_rewards (id);

CREATE INDEX ix_claimed_rewards_restaurant_id ON claimed_rewards (restaurant_id);

CREATE INDEX ix_claimed_rewards_uid ON claimed_rewards (uid);

CREATE TABLE loyalty (
    id SERIAL NOT NULL, 
    uid VARCHAR, 
    restaurant_id VARCHAR, 
    total_points INTEGER, 
    restaurant_points INTEGER, 
    tier VARCHAR, 
    punches INTEGER, 
    redemption_history JSON, 
    visited_restaurants JSON, 
    last_spin_time TIMESTAMP WITHOUT TIME ZONE, 
    spin_history JSON, 
    referral_codes JSON, 
    referrals_made JSON, 
    referred_by JSON, 
    PRIMARY KEY (id), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id), 
    FOREIGN KEY(uid) REFERENCES users (uid)
);

CREATE INDEX ix_loyalty_id ON loyalty (id);

CREATE INDEX ix_loyalty_restaurant_id ON loyalty (restaurant_id);

CREATE INDEX ix_loyalty_uid ON loyalty (uid);

CREATE TABLE submissions (
    submission_id SERIAL NOT NULL, 
    uid VARCHAR, 
    restaurant_id VARCHAR, 
    amount_spent FLOAT, 
    points_earned INTEGER, 
    submitted_at TIMESTAMP WITHOUT TIME ZONE, 
    PRIMARY KEY (submission_id), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id), 
    FOREIGN KEY(uid) REFERENCES users (uid)
);

CREATE INDEX ix_submissions_restaurant_id ON submissions (restaurant_id);

CREATE INDEX ix_submissions_submission_id ON submissions (submission_id);

CREATE INDEX ix_submissions_uid ON submissions (uid);

UPDATE alembic_version SET version_num='2e38b4c5d7c0' WHERE alembic_version.version_num = 'bb8c1ff5c2eb';

-- Running upgrade 2e38b4c5d7c0 -> e4c3ec824012

ALTER TABLE users ADD COLUMN role VARCHAR;

UPDATE alembic_version SET version_num='e4c3ec824012' WHERE alembic_version.version_num = '2e38b4c5d7c0';

-- Running upgrade e4c3ec824012 -> order_id_format_change

CREATE TABLE promo_codes (
    id SERIAL NOT NULL, 
    code VARCHAR, 
    description VARCHAR, 
    discount_percent FLOAT, 
    discount_amount FLOAT, 
    active BOOLEAN DEFAULT '1', 
    valid_from TIMESTAMP WITHOUT TIME ZONE, 
    valid_to TIMESTAMP WITHOUT TIME ZONE, 
    usage_limit INTEGER, 
    used_count INTEGER DEFAULT '0', 
    restaurant_id VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id)
);

CREATE INDEX ix_promo_codes_id ON promo_codes (id);

CREATE UNIQUE INDEX ix_promo_codes_code ON promo_codes (code);

CREATE TABLE menu_categories (
    id SERIAL NOT NULL, 
    restaurant_id VARCHAR NOT NULL, 
    name VARCHAR NOT NULL, 
    description VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    CONSTRAINT uq_menu_categories_name UNIQUE (name), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id)
);

CREATE INDEX ix_menu_categories_restaurant_id ON menu_categories (restaurant_id);

CREATE INDEX ix_menu_categories_id ON menu_categories (id);

CREATE TABLE menu_items (
    id SERIAL NOT NULL, 
    restaurant_id VARCHAR NOT NULL, 
    name VARCHAR NOT NULL, 
    description VARCHAR, 
    price FLOAT NOT NULL, 
    available BOOLEAN DEFAULT '1', 
    category_id INTEGER, 
    image_url VARCHAR, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id), 
    FOREIGN KEY(category_id) REFERENCES menu_categories (id)
);

CREATE INDEX ix_menu_items_id ON menu_items (id);

CREATE TABLE orders_new (
    id VARCHAR NOT NULL, 
    user_id VARCHAR NOT NULL, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    status VARCHAR DEFAULT 'Pending', 
    total_cost FLOAT NOT NULL, 
    payment_status VARCHAR DEFAULT 'Pending', 
    promo_code_id INTEGER, 
    restaurant_id VARCHAR, 
    restaurant_name VARCHAR, 
    order_number INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (uid), 
    FOREIGN KEY(promo_code_id) REFERENCES promo_codes (id), 
    FOREIGN KEY(restaurant_id) REFERENCES restaurants (restaurant_id)
);

CREATE INDEX ix_orders_new_id ON orders_new (id);

CREATE TABLE order_items_new (
    id SERIAL NOT NULL, 
    order_id VARCHAR, 
    item_id INTEGER, 
    quantity INTEGER DEFAULT '1', 
    price FLOAT NOT NULL, 
    options JSON, 
    PRIMARY KEY (id), 
    FOREIGN KEY(order_id) REFERENCES orders_new (id), 
    FOREIGN KEY(item_id) REFERENCES menu_items (id)
);

CREATE INDEX ix_order_items_new_id ON order_items_new (id);

CREATE TABLE order_status_history_new (
    id SERIAL NOT NULL, 
    order_id VARCHAR NOT NULL, 
    status VARCHAR NOT NULL, 
    changed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    changed_by VARCHAR NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(order_id) REFERENCES orders_new (id)
);

CREATE INDEX ix_order_status_history_new_id ON order_status_history_new (id);

CREATE TABLE payments_new (
    id SERIAL NOT NULL, 
    order_id VARCHAR NOT NULL, 
    amount FLOAT NOT NULL, 
    method VARCHAR NOT NULL, 
    status VARCHAR DEFAULT 'Pending', 
    processed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    paid_at TIMESTAMP WITHOUT TIME ZONE, 
    transaction_id VARCHAR, 
    PRIMARY KEY (id), 
    FOREIGN KEY(order_id) REFERENCES orders_new (id)
);

CREATE INDEX ix_payments_new_id ON payments_new (id);

ALTER TABLE orders_new RENAME TO orders;

ALTER TABLE order_items_new RENAME TO order_items;

ALTER TABLE order_status_history_new RENAME TO order_status_history;

ALTER TABLE payments_new RENAME TO payments;

UPDATE alembic_version SET version_num='order_id_format_change' WHERE alembic_version.version_num = 'e4c3ec824012';

-- Running upgrade order_id_format_change -> 23a1f18eb6c5

SELECT name FROM sqlite_master WHERE type='table' AND name='menu_categories';

