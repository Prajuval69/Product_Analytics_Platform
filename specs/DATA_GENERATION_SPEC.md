# Synthetic Data Generation Specification

Generate deterministic synthetic SaaS/product data.

Default scale:
- 10,000 users
- 5 products
- 15 features
- 6–12 months of events
- 500,000+ events if runtime is acceptable
- subscriptions
- transactions
- support tickets

Generate realistic distributions for:
- signup dates
- acquisition channels
- countries/regions
- device/platform
- plans
- feature usage
- session activity
- purchases
- support tickets

Introduce controlled correlations:
- engaged users are more likely to convert
- sustained low engagement increases churn likelihood
- higher plans have different usage/revenue patterns

Keep the random seed configurable. Never embed the target label directly in the predictive feature set.

Include a controlled data-quality fixture containing examples of duplicates, nulls, invalid categories or broken relationships for testing. Do not mix bad fixtures into the production synthetic dataset unless explicitly documented.
