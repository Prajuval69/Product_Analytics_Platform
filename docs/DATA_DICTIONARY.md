# Data dictionary

The authoritative typed source DDL is `sql/raw.sql`; source columns are also declared in `TABLE_COLUMNS` in `src/platform_app/generate.py`. dbt's `models/schema.yml` records every model's grain and key tests. Raw primary keys are positive synthetic integers; foreign keys constrain user/product and feature/product ownership. All timestamps are timezone-aware UTC.

| Source | Grain/key | Attributes |
|---|---|---|
| raw.products | product_id | product_name; category=SaaS |
| raw.features | feature_id | product_id; feature_name; is_key_feature; three features per product |
| raw.users | user_id | primary product_id; signup_at; acquisition_channel (organic/paid_search/referral/social/partner); country (US/GB/IN/DE/CA/AU); immutable plan (free/starter/pro/enterprise); device (web/ios/android) |
| raw.events | event_id | user_id; product_id; nullable feature_id; explicit session_id; event_at; event_type; device; JSON properties with synthetic provenance/schema version |
| raw.subscriptions | subscription_id | user_id; product_id; plan; started_at; nullable cancelled_at; monthly_price; status (active/cancelled) |
| raw.transactions | transaction_id | subscription_id; user_id; product_id; transaction_at; amount; currency=USD; status (succeeded/failed) |
| raw.support_tickets | ticket_id | user_id; product_id; opened_at; nullable resolved_at; priority (low/medium/high); category (billing/bug/how_to) |

Staging preserves these natural keys and standardizes categories. Added columns: `signup_date`, `event_date`, `is_active`, `transaction_date`, `recognized_revenue`, `resolution_hours`. Null feature_id is intentional for non-feature events; null cancelled_at means ongoing; null resolved_at means unresolved. Staging does not silently deduplicate invalid source records: raw constraints and quality checks reject them.

| Intermediate | Grain | Main derived fields |
|---|---|---|
| int_user_daily_activity | user/product/active date | active_event_count, distinct sessions, feature_diversity, first/last event timestamps |
| int_user_feature_usage | user/feature/month/plan | use_count, first_used_at, last_used_at |
| int_user_sessions | session_id | user/product/date/device, start/end, event_count, is_active, duration_seconds |
| int_user_funnel | user_id | signup attributes, onboarding_at, activation_at, feature_at, purchase_at |
| int_user_revenue | user_id | lifetime_revenue, paid_transactions, last_payment_at |
| int_customer_health | user_id at history end | recency, sessions_30d, active_days_30d, lifetime revenue, ticket/open-ticket counts, lifecycle_status, customer_segment |
| int_churn_features | user_id/cutoff_date | tenure_days, sessions_30d, active_days_30d, event_count_30d, days_since_last_activity, feature_diversity, key_feature_uses, revenue_30d, support_tickets_30d, subscription_tenure_days, plan; nullable future churned label |

Dimensions: dim_user includes user_key and product_key plus signup and lifecycle attributes; dim_product and dim_feature contain stable surrogate/natural keys and names; dim_date includes YYYYMMDD date_key, UTC date, ISO weekday, week/month starts, month, quarter, year and weekend flag. MD5 keys encode entity namespaces for deterministic joins and are not cryptographic anonymization claims.

Fact rows preserve staging columns plus entity-specific surrogate primary key, user_key, product_key and date_key. fct_events additionally has a nullable feature_key. fct_sessions uses the explicit source session grain rather than a 30-minute inferred session. Sources are sorted by user generation, not globally by timestamp; SQL always uses timestamps for chronology.

Analytical mart keys and fields: product metrics (metric_key, date/product, numerator/denominator KPIs and revenue); funnel (funnel_key, segment/step/entrants/conversion/dropoff); retention (cohort_key, month/product/channel/offset/cohort_size/eligible_users/retained_users/retention_rate); adoption (adoption_key, month/feature/plan/eligible/adopted/use counts); health (user_key/current health); predictions (user_id/user_key/product/plan/channel/country/segment/probability/band/scoring_date/model_version).

Operational tables: `control.run_config` is one row with seed, source horizon and loaded_at; `control.ml_predictions` is one current score per eligible user; `reporting.data_quality` is one latest result per named check with passed, observed_value and checked_at. This is current-state monitoring, not a historical incident log.
