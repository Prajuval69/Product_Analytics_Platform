# Airflow Specification

Create an idempotent DAG named `product_analytics_pipeline`.

Suggested task groups:
1. `generate_data`
2. `load_raw`
3. `dbt_staging`
4. `dbt_intermediate`
5. `dbt_marts`
6. `dbt_tests`
7. `train_churn_model`
8. `export_bi`
9. `final_validation`

Requirements:
- retries for transient tasks
- clear task IDs
- useful logs
- environment-based configuration
- no credentials committed
- dependency ordering
- failure should stop downstream tasks
- reruns should not duplicate data unexpectedly

Provide Docker-based local startup where practical.
