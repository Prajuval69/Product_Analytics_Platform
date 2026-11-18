# dbt implementation

The project uses dbt Core 1.9.10 and dbt-postgres 1.9.0, with no external dbt packages. `profiles.yml` contains environment references, never literal credentials. The CLI imports `.env` before launching dbt. An explicit schema macro yields `staging`, `intermediate` and `marts` rather than dbt's default target-prefixed custom schema names; use a dedicated local database to avoid collisions.

Seven staging views clean raw fields and centrally classify active events. Seven intermediate tables persist reusable computations. Daily activity has a unique user/date index and a product/date index, enabling rolling metrics and temporal eligibility lookups. Raw event/user and subscription/transaction/support timestamps are indexed to support as-of feature queries.

Four dimensions, five facts and six analytical marts satisfy the master specification. All fact grains and model descriptions are in `models/schema.yml`; sources are in `models/sources.yml`. The scoring mart is a view over the Python-populated control table, so subsequent scoring updates appear immediately. Other marts use table materialization for straightforward reproducibility. No artificial incremental model is included.

`dbt build` runs transformations and tests together. The pipeline also runs `dbt test` after scoring to validate populated prediction output. Generic tests cover unique/not-null keys, relationships and allowed categories; custom SQL tests reject metric bounds, non-monotone funnels, temporal/product mismatches, immature labels, duplicate composite grains, invoice lifecycle violations and revenue disagreement. Raw invalid fixtures never enter production source generation.

Run wrapper commands `dbt-parse`, `dbt-build`, `dbt-test`, `dbt-docs` through `platform_app.cli`. Airflow splits runs into staging/intermediate/marts while preserving dependencies. `docs generate` produces catalog.json, manifest.json and index.html in `dbt/target`; these generated files are ignored. `scripts/write_dbt_schema.py` regenerates the committed grain/test schema and consolidates tests when natural primary keys also need relationships.
