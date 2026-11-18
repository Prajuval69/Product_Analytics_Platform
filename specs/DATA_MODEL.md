# Data Model Specification

## Grain
Document the grain of every table in dbt schema files and README.

## Dimensions
### dim_user
One row per user. Include user key, signup date, acquisition channel, geography, plan, lifecycle attributes and current status.

### dim_product
One row per product.

### dim_feature
One row per product feature.

### dim_date
One row per calendar date with day/week/month/quarter/year attributes.

## Facts
### fct_events
One row per product event.

### fct_sessions
One row per user session.

### fct_transactions
One row per transaction.

### fct_subscriptions
One row per subscription lifecycle record or documented subscription grain.

### fct_support_tickets
One row per support interaction.

## Marts
- mart_product_metrics: daily product KPIs.
- mart_funnel_analysis: funnel step performance.
- mart_retention_cohorts: cohort/date retention matrix.
- mart_feature_adoption: feature-level adoption and usage.
- mart_customer_health: customer engagement, revenue and support indicators.
- mart_churn_predictions: model scores and risk bands.

Use consistent keys and avoid duplicating business logic across marts.
