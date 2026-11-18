# Troubleshooting

| Symptom | Action |
|---|---|
| No PostgreSQL binaries | Install PostgreSQL 16+ or use Docker; set PG_BIN to its bin directory |
| Port 55432 busy | Stop the project native cluster before Docker; for native clients update PG_PORT and restart that cluster |
| Connection/authentication fails | Confirm the process and .env refer to the same host/port/user/database; .env changes do not change existing role passwords |
| dbt works through CLI but fails directly | Direct dbt does not load .env; export its values or use the CLI wrapper |
| dbt test names collide after schema editing | Consolidate each column's test declarations; regenerate with scripts/write_dbt_schema.py |
| Source checksum/config mismatch | Run generate again; never hand-edit generated production CSVs |
| Model split lacks both classes/20 examples | Increase SYNTHETIC_USERS; default 10,000 is the verified workload |
| Empty/current prediction output | Check eligibility and source horizon; only currently active, mature, non-cancelled customers are scored |
| Airflow missing/unsupported on Windows | Use the Docker deployment or native shared-task CLI; a scheduler run cannot be claimed from static syntax checks |
| DAG import failure in Linux | Run airflow dags list-import-errors; confirm image/version and DAG directory; do not install dbt into Airflow's base Python |
| Power BI totals look too large | Use measures that sum numerators/denominators; do not sum active-user counts across dates or MRR over time |
| BI data-quality manifest disagrees | Run export then verify; final validation refreshes the quality extract and manifest |

Use `.runtime/` local command logs, `dbt/logs/dbt.log`, `outputs/verification/pipeline_run.json`, dbt run_results.json, and Airflow task logs to locate failure stages. Full-refresh marts from an interrupted run may be partially updated; rerun the pipeline before consuming them. Do not run native CLI and Airflow concurrently against one database.

Native `.runtime/pgdata` is the working database, not a disposable cache while the server is running. Stop with the provided script before deliberately removing or relocating a project cluster. Docker volumes persist across `down`; deleting them destroys local warehouse/metadata state.
