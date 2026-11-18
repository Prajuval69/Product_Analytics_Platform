# MASTER PROMPT — Product Analytics & Data Modelling Platform

## Mission
Build a complete, production-style portfolio project named **Product Analytics & Data Modelling Platform** from this workspace. Work from start to finish without asking for implementation decisions unless a genuinely blocking ambiguity exists. Inspect every specification file in `specs/` and `docs/` before coding.

The project must demonstrate practical competence in SQL, dimensional data modelling, PostgreSQL, dbt, Airflow, Python, data quality, product analytics, cohort/funnel analysis, basic machine learning, testing, documentation, and BI-ready outputs.

The project must be runnable locally with no paid services and no external credentials. Use synthetic data only. Do not fabricate external business results.

## Core outcome
Create an end-to-end pipeline:

Synthetic product events / customers / subscriptions / support data
→ ingestion
→ PostgreSQL raw layer
→ Airflow orchestration
→ dbt staging/intermediate/marts
→ data-quality checks
→ product analytics metrics
→ churn prediction model
→ BI-ready reporting tables and CSV outputs
→ tests + documentation + reproducible run instructions.

## Mandatory requirements
1. Read all files in `specs/` and `docs/` first.
2. Inspect the workspace before creating files.
3. Implement the complete project, not a skeleton or pseudocode.
4. Generate realistic synthetic data deterministically with a configurable seed.
5. Use PostgreSQL as the primary warehouse/database.
6. Use dbt for transformations and dimensional modelling.
7. Use Airflow for orchestration.
8. Implement clear raw, staging, intermediate and mart layers.
9. Implement data-quality checks using dbt tests and Python checks where appropriate.
10. Build product analytics metrics: DAU, WAU, MAU, activation, feature adoption, funnels, retention/cohorts, churn, revenue and ARPU.
11. Train at least one basic churn model with scikit-learn.
12. Avoid target leakage in the ML dataset.
13. Produce BI-ready tables and exportable CSV outputs.
14. Include a comprehensive automated test suite.
15. Run the complete pipeline and fix errors before declaring completion.
16. Verify that the database, dbt models, tests, ML artifacts and reporting outputs are actually generated.
17. Provide clear documentation explaining architecture and how to run everything.
18. Do not require Power BI Desktop to execute the core project. Provide CSV/reporting outputs that can be imported into Power BI manually.
19. Do not claim Amplitude/Mixpanel integration. Instead implement equivalent event/funnel/cohort concepts locally.
20. Do not use real customer or company data.

## Preferred stack
- Python 3.11+
- PostgreSQL 16+
- dbt-postgres
- Apache Airflow 2.x/3.x compatible with the selected implementation
- Pandas / NumPy
- scikit-learn
- pytest
- SQLAlchemy or psycopg
- Docker Compose where practical
- Power BI-compatible CSV outputs

If local environment limitations make native Airflow installation difficult, provide Docker Compose as the primary reproducible path. Do not replace Airflow with a homemade scheduler.

## Architecture
Implement these layers:

### Raw
- raw.users
- raw.products
- raw.features
- raw.events
- raw.subscriptions
- raw.transactions
- raw.support_tickets

### Staging
- stg_users
- stg_products
- stg_features
- stg_events
- stg_subscriptions
- stg_transactions
- stg_support_tickets

### Intermediate
- int_user_daily_activity
- int_user_feature_usage
- int_user_sessions
- int_user_funnel
- int_user_revenue
- int_customer_health
- int_churn_features

### Marts
- dim_user
- dim_product
- dim_feature
- dim_date
- fct_events
- fct_sessions
- fct_transactions
- fct_subscriptions
- fct_support_tickets
- mart_product_metrics
- mart_funnel_analysis
- mart_retention_cohorts
- mart_feature_adoption
- mart_customer_health
- mart_churn_predictions

Use surrogate keys where appropriate and document grain for every fact table.

## Product event model
Generate realistic event types such as:
- signup
- login
- onboarding_started
- onboarding_completed
- feature_viewed
- feature_used
- search
- report_created
- export_completed
- invite_sent
- invite_accepted
- upgrade_started
- purchase_completed
- support_opened
- churn_signal

Include event timestamp, user, session, product, feature, device/platform and useful event properties.

## Business logic
Define and document metric formulas. At minimum:
- DAU = distinct active users per day
- WAU = distinct active users over a rolling 7-day window
- MAU = distinct active users over a rolling 30-day window
- Activation = users completing the defined activation event within the activation window / eligible signups
- Feature adoption = users using a feature / eligible active users
- Funnel conversion = users reaching a step / users entering the funnel
- D7/D30 retention = users active on target day / users in cohort
- Churn = users meeting the documented churn definition during the measurement window
- ARPU = revenue / active or paying users according to documented definition

Make all definitions explicit and consistent across SQL, Python and documentation.

## Data generation
Create configurable deterministic synthetic data with enough scale to make the project meaningful while remaining laptop-friendly. Default target:
- 10,000 users
- 5 products
- 12–20 features
- 6–12 months of event history
- 100,000+ events minimum; preferably 500,000+ if runtime remains reasonable
- subscriptions and transactions
- support interactions

Create realistic correlations such as lower engagement increasing churn probability, but ensure the ML target is not directly encoded in predictive features.

## Airflow DAG
Create a DAG that orchestrates:
1. Generate/prepare synthetic source data
2. Load raw tables
3. Run dbt staging/intermediate/mart models
4. Run dbt tests
5. Build ML feature dataset
6. Train/evaluate churn model
7. Export reporting datasets
8. Run final validation

Tasks must have sensible dependencies, retries, logging and failure handling. Make the DAG idempotent.

## dbt
Use a real dbt project with:
- profiles configuration strategy that works locally without committing secrets
- sources
- staging models
- intermediate models
- marts
- schema.yml files
- tests: not_null, unique, relationships, accepted_values where appropriate
- custom business tests for key metrics/data-quality rules
- documentation for important models and columns

Prefer incremental models only where they add genuine value; correctness and simplicity are more important than artificial complexity.

## ML
Build a basic churn prediction workflow.

Requirements:
- clearly define prediction observation window and prediction horizon
- prevent future information leakage
- create reproducible train/test split using time where appropriate
- baseline model: Logistic Regression
- optional comparison: Random Forest
- metrics: ROC-AUC, precision, recall, F1 and confusion matrix
- class imbalance handling where justified
- feature importance / coefficients
- save model and feature metadata
- create a scoring table containing user_id, churn_probability, risk_band and scoring_date

Do not optimize for an impressive metric through leakage or unrealistic synthetic generation.

## BI outputs
Create exportable datasets under `outputs/bi/` for:
1. Executive KPI overview
2. Product funnel
3. Retention cohorts
4. Feature adoption
5. Customer health/churn
6. Revenue/subscription analytics
7. Data-quality monitoring

Include a Power BI dashboard specification in documentation with recommended pages, visuals, slicers and relationships. Do not pretend a `.pbix` file was generated if the environment cannot create one.

## Testing
Include:
- Python unit tests
- data-generation tests
- dbt tests
- ML pipeline tests
- integration/smoke tests where practical
- final end-to-end verification script

Test both expected success cases and intentionally invalid data where appropriate.

## Documentation
Create:
- README.md
- architecture documentation
- setup guide
- data dictionary
- metric definitions
- dbt model documentation
- Airflow DAG documentation
- ML methodology
- BI/dashboard guide
- troubleshooting guide
- portfolio/interview explanation

The interview guide should explain the project in simple language and include likely questions about data modelling, dbt, Airflow, SQL, product analytics, ML, testing and tradeoffs.

## Code quality
Use:
- modular Python
- type hints where useful
- meaningful names
- configuration via environment variables
- no hard-coded secrets
- structured logging
- sensible error handling
- lint/format configuration where practical
- `.gitignore`
- `.env.example`

Do not over-engineer. Every component should have a clear purpose.

## Required final verification
Before completion:
1. Run Python tests.
2. Run dbt parse/build/test.
3. Start required services.
4. Execute the Airflow workflow or a documented equivalent trigger path.
5. Verify row counts in key tables.
6. Verify all required BI exports exist and are non-empty.
7. Verify ML model/artifacts exist.
8. Verify no secrets are committed.
9. Verify README commands are accurate.
10. Fix failures and rerun.
11. Generate `FINAL_VERIFICATION.md` containing exact commands run, results, row counts, test counts, generated artifacts and any environment-specific limitations.

## Final deliverable standard
The repository should look like a serious junior data/analytics engineering portfolio project that a recruiter can inspect. It must be possible for another person to clone it, follow the README, start the services, run the pipeline, inspect the SQL/dbt models, and consume the resulting BI datasets.

Do not stop after writing files. Build, execute, test, debug and verify the project.
