CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS control;
CREATE SCHEMA IF NOT EXISTS reporting;
CREATE TABLE IF NOT EXISTS raw.products (
 product_id bigint PRIMARY KEY, product_name text NOT NULL, category text NOT NULL
);
CREATE TABLE IF NOT EXISTS raw.features (
 feature_id bigint PRIMARY KEY, product_id bigint NOT NULL REFERENCES raw.products,
 feature_name text NOT NULL, is_key_feature boolean NOT NULL,
 UNIQUE(feature_id, product_id)
);
CREATE TABLE IF NOT EXISTS raw.users (
 user_id bigint PRIMARY KEY, product_id bigint NOT NULL REFERENCES raw.products,
 signup_at timestamptz NOT NULL, acquisition_channel text NOT NULL, country text NOT NULL,
 plan text NOT NULL CHECK(plan IN ('free','starter','pro','enterprise')),
 device text NOT NULL CHECK(device IN ('web','ios','android')), UNIQUE(user_id,product_id)
);
CREATE TABLE IF NOT EXISTS raw.events (
 event_id bigint PRIMARY KEY, user_id bigint NOT NULL, product_id bigint NOT NULL,
 feature_id bigint, session_id text NOT NULL, event_at timestamptz NOT NULL,
 event_type text NOT NULL CHECK(event_type IN ('signup','login','onboarding_started','onboarding_completed','feature_viewed','feature_used','search','report_created','export_completed','invite_sent','invite_accepted','upgrade_started','purchase_completed','support_opened','churn_signal')),
 device text NOT NULL CHECK(device IN ('web','ios','android')), properties jsonb NOT NULL,
 FOREIGN KEY(user_id,product_id) REFERENCES raw.users(user_id,product_id),
 FOREIGN KEY(feature_id,product_id) REFERENCES raw.features(feature_id,product_id)
);
CREATE TABLE IF NOT EXISTS raw.subscriptions (
 subscription_id bigint PRIMARY KEY, user_id bigint NOT NULL, product_id bigint NOT NULL,
 plan text NOT NULL CHECK(plan IN ('starter','pro','enterprise')), started_at timestamptz NOT NULL,
 cancelled_at timestamptz, monthly_price numeric(12,2) NOT NULL CHECK(monthly_price > 0),
 status text NOT NULL CHECK(status IN ('active','cancelled')),
 CHECK(cancelled_at IS NULL OR cancelled_at > started_at),
 FOREIGN KEY(user_id,product_id) REFERENCES raw.users(user_id,product_id)
);
CREATE TABLE IF NOT EXISTS raw.transactions (
 transaction_id bigint PRIMARY KEY, subscription_id bigint NOT NULL REFERENCES raw.subscriptions,
 user_id bigint NOT NULL, product_id bigint NOT NULL, transaction_at timestamptz NOT NULL,
 amount numeric(12,2) NOT NULL CHECK(amount >= 0), currency text NOT NULL CHECK(currency='USD'),
 status text NOT NULL CHECK(status IN ('succeeded','failed')),
 FOREIGN KEY(user_id,product_id) REFERENCES raw.users(user_id,product_id)
);
CREATE TABLE IF NOT EXISTS raw.support_tickets (
 ticket_id bigint PRIMARY KEY, user_id bigint NOT NULL, product_id bigint NOT NULL,
 opened_at timestamptz NOT NULL, resolved_at timestamptz, priority text NOT NULL CHECK(priority IN ('low','medium','high')),
 category text NOT NULL CHECK(category IN ('billing','bug','how_to')),
 CHECK(resolved_at IS NULL OR resolved_at >= opened_at),
 FOREIGN KEY(user_id,product_id) REFERENCES raw.users(user_id,product_id)
);
CREATE INDEX IF NOT EXISTS events_user_time ON raw.events(user_id,event_at);
CREATE INDEX IF NOT EXISTS events_product_time ON raw.events(product_id,event_at);
CREATE INDEX IF NOT EXISTS subscriptions_user_time ON raw.subscriptions(user_id,started_at);
CREATE INDEX IF NOT EXISTS transactions_user_time ON raw.transactions(user_id,transaction_at);
CREATE INDEX IF NOT EXISTS tickets_user_time ON raw.support_tickets(user_id,opened_at);
CREATE TABLE IF NOT EXISTS control.run_config (
 singleton integer PRIMARY KEY CHECK(singleton=1), seed integer NOT NULL,
 history_start date NOT NULL, history_end date NOT NULL, loaded_at timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS control.ml_predictions (
 user_id bigint PRIMARY KEY REFERENCES raw.users, churn_probability double precision NOT NULL CHECK(churn_probability BETWEEN 0 AND 1),
 risk_band text NOT NULL CHECK(risk_band IN ('low','medium','high')),
 scoring_date date NOT NULL, model_version text NOT NULL
);
CREATE TABLE IF NOT EXISTS reporting.data_quality (
 check_name text PRIMARY KEY, passed boolean NOT NULL, observed_value text NOT NULL,
 checked_at timestamptz NOT NULL
);
