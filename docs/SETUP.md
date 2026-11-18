# Setup and reproducibility

The README contains complete Windows and Docker commands. Python supports 3.11 and 3.12. `requirements.lock` freezes resolved runtime and test dependencies; use it rather than installing unrelated globally available packages. Install the editable project afterward with `--no-deps`.

Configure `SYNTHETIC_SEED`, `SYNTHETIC_USERS`, `HISTORY_START`, `HISTORY_END`, `PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD` and `DBT_THREADS` in `.env`. Minimum generation configuration is 10 users and 181 calendar days. Temporal model training also requires at least 20 examples of both outcome classes in each labeled split; 1,000+ users is recommended for smoke workloads and 10,000 is the verified default. A changed horizon/seed requires regeneration before loading.

`scripts/local_postgres.ps1 start` uses PostgreSQL binaries already installed on Windows, creates `.runtime/pgdata`, initializes scram authentication with a randomly generated ignored password, and starts only that cluster. `stop` shuts down only that cluster. The helper uses the fixed native database name `analytics` and host `127.0.0.1`; the Python/dbt clients support configurable database settings. Use the Docker path for a complete Airflow deployment. Stop the native cluster before starting Docker's warehouse on the same port.

Compose requires three local passwords in `.env`. Choose alphanumeric passwords for the Airflow metadata URL; do not use credentials from another service. Named volumes persist databases. A password change in `.env` does not automatically alter a previously initialized PostgreSQL role; reset it with SQL or start with a new volume intentionally.

Native Linux users create an `analytics` PostgreSQL database and role independently and supply matching configuration. Airflow's chosen version is supported on Linux; Windows without WSL/Docker cannot execute it. The project does not attempt to install WSL or change system services.

Default simulation dates describe a closed historical dataset, not the current date. BI activity freshness shows source history end; ingestion freshness shows actual load time. Both are needed to interpret the result.
