# Architecture

The repository deliberately separates orchestration from transformation. Airflow is responsible for task ordering, retry, failure propagation and logs. PostgreSQL owns storage, constraints and transactional replacement. dbt owns SQL transformations and canonical metrics. Python owns synthetic source simulation, COPY ingestion, scikit-learn and exports.

1. `generate` writes seven deterministic CSV files and a SHA-256/count manifest. The seed and fixed date horizon make fresh runs repeatable. Invalid test fixtures live in a separate directory.
2. `load` validates configuration and checksums before opening a transaction. It creates source structures, truncates the seven sources together with predictions, COPY-loads parents before children, checks counts, runs ANALYZE and updates the source horizon. An error rolls back the replacement.
3. `quality` checks record counts, product relationships, timestamps, signup completeness and operational ingestion freshness.
4. dbt builds UTC staging views, indexed daily activity, reusable intermediate data, dimensions, facts and analytical marts. Key relationships are enforced by dbt tests and raw foreign keys. dbt builds relations transactionally; consumers should read only after pipeline success because a multi-model build is not globally atomic.
5. ML reads only `intermediate.int_churn_features`, uses an explicit predictor allowlist and temporal evaluation, persists an evaluated model, and atomically replaces `control.ml_predictions`. A dbt view exposes the latest scores without rebuilding marts.
6. A second dbt test pass covers populated predictions. Reporting exports flatten analysis tables; final validation independently reconciles raw activity and revenue, verifies model loading and reporting files, and refreshes the quality extract.

Airflow has 14 sequential tasks and `max_active_runs=1`. The CLI executes the same operations synchronously on native Windows. Manual CLI execution must not overlap a DAG run. Native execution has no substitute scheduling engine.

Schemas: `raw` (seven sources), `control` (source horizon and scores), `staging` (seven views), `intermediate` (seven tables), `marts` (14 tables and one prediction view), `reporting` (quality results). Airflow metadata uses a separate PostgreSQL instance in Compose.

The analytics virtual environment is separate from Airflow's Python packages to avoid dbt/SQLAlchemy/provider dependency collisions. Docker uses mounted source data, output directories and named warehouse/metadata/dbt/log volumes. Passwords are environment-provided and services bind only to loopback on the host.

Scaling path: move raw append ingestion behind a watermark/CDC contract, partition events by date, use incremental dbt with late-arrival corrections, deploy a columnar warehouse for high-volume metrics, add model registry/drift checks, restrict loader/transformer/reader roles and publish atomic reporting snapshots. These are future changes, not implemented claims.
