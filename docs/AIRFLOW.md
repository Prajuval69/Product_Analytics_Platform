# Airflow orchestration

The real `product_analytics_pipeline` DAG targets Apache Airflow 2.10.5 on Linux, using BashOperator and LocalExecutor. It is manually triggered (`schedule=None`), has a UTC start date, no catchup, a single active run, two retries per task, one-minute retry delay and 45-minute task timeout. Failed tasks stop all downstream work under the default all-success trigger rule.

Tasks, in order: generate_data → load_raw → validate_raw → dbt_parse → dbt_staging → dbt_intermediate → dbt_marts → dbt_tests → build_ml_features → train_churn_model → dbt_final_tests → export_bi → final_validation → dbt_documentation.

Each task starts a fresh process from the isolated `/opt/analytics-venv` and calls the same CLI implementation used natively. The DAG does no work at import time and embeds no credentials. Commands use fixed task arguments; user-provided Jinja command interpolation is not used. Airflow captures normal logs and nonzero process exits; Python logs task status as JSON and preserves exceptions.

Idempotence: generation is seed/horizon-repeatable, raw replacement is transactional, dbt full-refresh table/view materializations replace outputs, ML scores replace a snapshot atomically, and each CSV replaces its predecessor. Airflow retries can repeat a task without duplicating rows. A complete run changes operational timestamps; model serialization hashes can vary with library versions and are artifact IDs rather than semantic source hashes.

See the README Docker commands to build, initialize metadata/admin, run scheduler/webserver, inspect import errors, execute `airflow dags test`, and trigger a normal run. Run the dedicated real DagBag test with `docker compose exec airflow-scheduler python -m pytest /opt/platform/airflow/tests -q`. The image includes pytest in Airflow's base interpreter for this isolated test. Analytics unit/integration tests run in `/opt/analytics-venv`; its optional Airflow test skips when the Airflow runtime is absent.

On the verified Windows host, Docker and WSL were unavailable; therefore DAG syntax/structure was checked, but no scheduler, DagBag import or DAG execution is claimed. Native execution uses the synchronous shared-task CLI. This limitation is also recorded in FINAL_VERIFICATION.md.

Initialization uses the official image's `_AIRFLOW_DB_MIGRATE` and `_AIRFLOW_WWW_USER_CREATE` entrypoint settings; passwords come from `.env`. See [the Airflow image entrypoint documentation](https://airflow.apache.org/docs/docker-stack/entrypoint.html) and [Airflow 2.10.5 DAG debugging](https://airflow.apache.org/docs/apache-airflow/2.10.5/core-concepts/debug.html).
