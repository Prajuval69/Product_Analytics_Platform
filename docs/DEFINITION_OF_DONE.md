# Definition of Done

The project is complete only when:

- [x] all specification files were read
- [x] source tree is organized
- [x] PostgreSQL startup works (native 18.3)
- [x] synthetic data generation works
- [x] raw ingestion works
- [x] dbt project parses
- [x] dbt build succeeds (29 models)
- [x] dbt tests pass (188)
- [ ] Airflow DAG loads successfully — real Linux DagBag test supplied; unavailable on this Windows host
- [ ] Airflow pipeline can execute end-to-end — Docker deployment supplied but not executed; shared-task native CLI succeeded
- [x] ML training succeeds
- [x] ML evaluation metrics are saved
- [x] BI exports are generated (13 CSVs)
- [x] Python tests pass (78 passed; one real Airflow import test skipped)
- [x] smoke/end-to-end verification passes (81 checks)
- [x] documentation is complete
- [x] `.env.example` exists
- [x] runtime passwords absent from source; secrets ignored (workspace has no Git commits to audit)
- [ ] temporary diagnostics/cache deletion — automatic approval review rejected cleanup with “blocked by policy”; these paths remain ignored
- [x] FINAL_VERIFICATION.md contains actual results

The two Airflow runtime acceptance checks remain environment-limited. Execute the README Docker commands on a Docker-capable host before claiming full Airflow verification. No PBIX assembly was performed or fabricated. Local caches and diagnostic logs remain because both batch and explicitly named cleanup commands were rejected by automatic approval review; they are excluded from the deliverable by .gitignore.
