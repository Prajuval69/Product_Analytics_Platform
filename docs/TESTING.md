# Testing

The project layers validation rather than equating a successful process exit with trustworthy data.

* Generator/unit tests prove seed reproducibility, varied seeds, primary grains, referential integrity, timestamps, invoice lifecycles and config rejection.
* Invalid fixtures test duplicates, null keys, missing required fields, categories, orphan keys, empty frames and checksum/config mismatch before database writes.
* ML tests verify purged temporal splits, class requirements, unknown-category handling, model persistence, leakage-prone column exclusion, band boundaries and a known confusion matrix.
* Pipeline tests check error propagation, the real DAG's static stage contract, Compose secret references, documented model inventory and optional real DagBag loading.
* PostgreSQL integration tests compare raw/fact counts, exercise database constraint rollback, independently recompute rolling activity/activation/retention in Python, reconcile analytical churn to SQL ML labels, and verify persisted scoring and every BI extract.
* dbt generic and singular tests cover transformations and business invariants; tests rerun after scoring.
* `analytics verify` checks all required relations, file/model artifacts, freshness, raw-to-mart activity and revenue and score population agreement. Outputs retain exact row counts and dbt test evidence.

Unit-only commands and full test commands appear in README. Integration tests are skipped unless `RUN_INTEGRATION=1`; run the pipeline first. Real Airflow import tests are skipped on Windows rather than emulating Airflow. Static DAG checks do not prove runtime import/execution. JUnit XML records pass/fail/skip counts; `FINAL_VERIFICATION.md` distinguishes actual execution from provided reproduction commands.
