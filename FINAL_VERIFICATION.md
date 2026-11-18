# Final verification

Recorded 2026-10-02T16:04:47.841146+05:30. Evidence comes from executed native PostgreSQL/Python/dbt tasks; business data is synthetic.

## Execution environment

- OS: Windows-11-10.0.26200-SP0; Python: 3.12.4.
- PostgreSQL: installed Windows PostgreSQL 18.3; isolated project cluster at 127.0.0.1:55432.
- Packages: `{"dbt-core": "1.9.10", "dbt-postgres": "1.9.0", "pandas": "2.2.3", "numpy": "2.1.3", "scipy": "1.15.3", "scikit-learn": "1.6.1", "pytest": "8.3.5", "psycopg": "3.2.9"}`.
- Docker executable and WSL Linux runtime unavailable; no native Windows Airflow runtime was installed.

## Final results

- Shared-task CLI pipeline: **success**.
- Python tests: **78 passed, 0 failed, 1 skipped**, 79 collected. The skip is real Airflow import on Windows.
- dbt: **29 models built**, **188 tests passed, 0 failed**; separate post-scoring test run.
- Final validation: **81 checks passed, 0 failed**.
- Reporting: **13 nonempty CSV extracts**, manifest and Power BI page/measure/relationship guide.
- Repository check: 99 source files parsed/scanned, zero runtime passwords found; .env and runtime outputs are ignored.
- Complete rerun: all seven source counts and SHA-256 checksums matched the preceding successful run (outputs/verification/idempotence.json).
- Lint and formatting checks were run separately; their exact commands appear below.

## Source records

| Source | Records |
|---|---:|
| products | 5 |
| features | 15 |
| users | 10,000 |
| events | 1,115,102 |
| subscriptions | 4,616 |
| transactions | 24,028 |
| support_tickets | 10,806 |
| **Total** | **1,164,572** |

## Warehouse row counts

| Relation | Rows |
|---|---:|
| intermediate.int_churn_features | 21,099 |
| intermediate.int_customer_health | 10,000 |
| intermediate.int_user_daily_activity | 180,993 |
| intermediate.int_user_feature_usage | 106,273 |
| intermediate.int_user_funnel | 10,000 |
| intermediate.int_user_revenue | 10,000 |
| intermediate.int_user_sessions | 206,917 |
| marts.dim_date | 273 |
| marts.dim_feature | 15 |
| marts.dim_product | 5 |
| marts.dim_user | 10,000 |
| marts.fct_events | 1,115,102 |
| marts.fct_sessions | 206,917 |
| marts.fct_subscriptions | 4,616 |
| marts.fct_support_tickets | 10,806 |
| marts.fct_transactions | 24,028 |
| marts.mart_churn_predictions | 3,921 |
| marts.mart_customer_health | 10,000 |
| marts.mart_feature_adoption | 540 |
| marts.mart_funnel_analysis | 2,300 |
| marts.mart_product_metrics | 1,365 |
| marts.mart_retention_cohorts | 865 |
| raw.events | 1,115,102 |
| raw.features | 15 |
| raw.products | 5 |
| raw.subscriptions | 4,616 |
| raw.support_tickets | 10,806 |
| raw.transactions | 24,028 |
| raw.users | 10,000 |
| staging.stg_events | 1,115,102 |
| staging.stg_features | 15 |
| staging.stg_products | 5 |
| staging.stg_subscriptions | 4,616 |
| staging.stg_support_tickets | 10,806 |
| staging.stg_transactions | 24,028 |
| staging.stg_users | 10,000 |

Also created control.run_config, control.ml_predictions and reporting.data_quality; counts and current checks are visible in operational exports.

## ML results

Logistic Regression trained on 2025-05-03 (4,395 rows), threshold-selected on 2025-07-02 (6,563 rows), and evaluated on 2025-08-31 (6,220 rows).

- ROC-AUC: 0.699066; precision: 0.609464; recall: 0.449348; F1: 0.517300.
- Confusion matrix [TN, FP; FN, TP]: `[[3156, 685], [1310, 1069]]`.
- Validation-selected threshold: 0.60; test prevalence: 0.382476.
- Current eligible scored users: 3,921; artifact version: 5eac19f7b4de.
- Model, features, metadata, coefficients, evaluation, test predictions and current scores were saved and the persisted model was reloaded/checked. No refit on test data; no claim of real-world predictive validity.

## Latest product metrics

| Product | DAU | WAU | MAU | Activation | Conversion | Churn | Daily revenue | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 50 | 290 | 861 | 72.33% | 27.42% | 37.53% | $1,135.00 | $22,251.00 |
| 2 | 48 | 300 | 877 | 73.20% | 27.75% | 35.67% | $825.00 | $23,952.00 |
| 3 | 38 | 248 | 802 | 71.75% | 29.72% | 40.36% | $608.00 | $24,299.00 |
| 4 | 54 | 266 | 804 | 71.82% | 27.53% | 41.87% | $1,012.00 | $22,086.00 |
| 5 | 61 | 338 | 894 | 72.30% | 27.11% | 35.93% | $486.00 | $22,361.00 |

Additional outputs: exact-day retention/cohorts, feature adoption, ARPU/ARPPU, revenue/subscriptions, customer segmentation, health and risk bands. See canonical definitions in docs/METRICS.md.

## Export inventory

| CSV | Rows |
|---|---:|
| executive_kpis.csv | 1,365 |
| product_funnel.csv | 2,300 |
| retention_cohorts.csv | 865 |
| feature_adoption.csv | 540 |
| customer_health.csv | 10,000 |
| churn_predictions.csv | 3,921 |
| revenue_subscriptions.csv | 24,028 |
| data_quality.csv | 82 |
| dim_date.csv | 273 |
| dim_product.csv | 5 |
| dim_user.csv | 10,000 |
| dim_feature.csv | 15 |
| subscriptions.csv | 4,616 |

## Commands actually executed

The final full run and test suite used these commands from the workspace root:

```powershell
.\scripts\local_postgres.ps1 start
uv pip compile pyproject.toml --extra dev --python-version 3.11 --output-file requirements.lock --quiet
uv pip sync --python .venv\Scripts\python.exe requirements.lock --quiet
uv pip install --python .venv\Scripts\python.exe --no-deps -e . --quiet
.venv\Scripts\python.exe scripts\write_dbt_schema.py
.venv\Scripts\python.exe -m platform_app.cli pipeline *> .runtime\pipeline-final.log
$env:RUN_INTEGRATION = '1'
.venv\Scripts\python.exe -m pytest -q --junitxml=outputs/verification/pytest.xml *> .runtime\tests-final.log
.venv\Scripts\ruff.exe check src scripts tests airflow
.venv\Scripts\ruff.exe format --check src scripts tests airflow
.venv\Scripts\python.exe scripts\verify_repository.py
.venv\Scripts\python.exe scripts\write_final_verification.py
```

The pipeline invokes dbt parse, dbt build, post-scoring dbt test and dbt docs generate with --project-dir dbt --profiles-dir dbt. It generated sources, loaded PostgreSQL, trained/scored ML, exported CSVs and ran final validation.

## Fixes and reruns

The first parse exposed duplicate not_null declarations on natural keys; the schema generator now merges column tests. The next build exposed a common-column ambiguity after a revenue join; an explicit product/date join fixed it. A subsequent KPI query was cancelled after query-plan inspection showed repeated nested-loop aggregate work; PostgreSQL MATERIALIZED CTEs ensure reusable aggregates execute once. All final errors were resolved and the complete pipeline and tests were rerun. A SciPy version mismatch warning was resolved by pinning 1.15.3, and the dependency lock was resolved for Python 3.11 to support Docker as well as native 3.12. The final test run produced no warnings.

## Environmental limits

- One real Airflow DAG with 14 tasks and a Docker deployment are provided. DAG syntax and static contract tests passed. Docker builds, DagBag import, scheduler startup and real DAG execution were **not executed** on this host; the standalone Airflow runtime test is available in airflow/tests for Linux. The shared-task CLI is the documented native execution path, not a replacement scheduler.
- Power BI report assembly was not executed; 13 verified CSVs and detailed dashboard/DAX instructions are delivered. No PBIX or dashboard screenshot was fabricated.
- The workspace did not initially contain a Git repository. Source scanning confirms no runtime passwords in the deliverable files; this is not a claim that a commit was audited.
- Generated datasets, warehouse state, model files, dbt compiled outputs and verification XML/JSON are intentionally ignored and retained locally as reproducible evidence. Automatic approval review rejected both batch and explicitly named cache deletion with the reason 'blocked by policy'. Temporary diagnostic files and caches therefore remain locally and are ignored; no cleanup success is claimed. Source specifications and this summary remain reviewable.

## Reproduction

Use the exact fresh-environment native or Docker commands in README.md. Docker-specific commands are provided reproduction instructions, not executed verification. The default source seed is 42; source checksums are recorded in data/generated/manifest.json. Change the seed/horizon deliberately and regenerate before loading.
