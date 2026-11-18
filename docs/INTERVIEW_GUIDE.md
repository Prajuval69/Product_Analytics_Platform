# Interview Guide

## 30-second explanation
“I built an end-to-end product analytics platform that takes synthetic product events and customer data, loads them into PostgreSQL, transforms them with dbt, orchestrates the workflow with Airflow, and produces dimensional models and product analytics marts. I then added a basic churn model and exported BI-ready datasets for Power BI. The main focus was reliable data modelling, repeatable pipelines and trusted product metrics.”

## Explain the architecture simply
Raw data is loaded first. Airflow controls the workflow. dbt cleans and transforms the data into staging, intermediate and mart layers. The marts answer product questions such as retention, funnels and feature adoption. A separate ML step uses only information available before the prediction cutoff to estimate churn risk. Finally, reporting tables are exported for Power BI.

## Likely questions
1. Why PostgreSQL?
2. Why dbt instead of putting all transformations in Python?
3. What does Airflow add?
4. What is the grain of your fact tables?
5. Why use fact and dimension tables?
6. How did you prevent ML leakage?
7. How did you define churn?
8. How did you calculate D7/D30 retention?
9. What tests did you implement?
10. How would you scale the pipeline?
11. What would you change for production?
12. How is this similar to Amplitude/Mixpanel?
13. Why use synthetic data?
14. How would you monitor pipeline failures?
15. How would you handle late-arriving events?

## Key tradeoffs to discuss
- PostgreSQL keeps the project locally reproducible.
- dbt centralizes SQL transformations and documentation.
- Airflow provides dependency management and retries.
- Synthetic data enables reproducibility but cannot establish real-world model performance.
- Power BI is treated as a consumption layer rather than embedding dashboard-specific logic into the pipeline.

## Concrete answers

1. **Why PostgreSQL?** Transactional COPY, constraints, timestamps, window functions and local installation handle the million-event demonstration. A columnar engine would suit larger histories.
2. **Why dbt?** SQL logic is versioned with dependencies, documentation and tests. Python does not duplicate the funnel/cohort implementations.
3. **What does Airflow add?** Fourteen tasks control retries, timeouts and dependencies. Native Windows execution uses the shared functions synchronously and does not prove an Airflow run.
4. **Fact grains?** Event, explicit session, invoice attempt, subscription lifetime and support ticket. Natural/surrogate keys remain visible; composite grains are tested.
5. **Dimensions?** Product, feature, user and UTC date. User plan is immutable and status uses type 1; no SCD2 history is claimed.
6. **Leakage?** Separate observation/outcome bounds, predictor allowlist, training-only scaler and 60-day-separated temporal snapshots.
7. **Churn?** Mature, recently active, not-yet-cancelled users; cancellation or zero future 30-day activity. Analytics and ML share the outcome macro.
8. **Retention?** Exact-day D7/D30 with maturity-adjusted denominators. Cohort size and eligible size are separate.
9. **Tests?** Generator determinism/invalid fixtures, raw constraints, dbt business/relationship tests, Python raw-data recomputation, temporal ML tests and artifact reconciliation.
10. **Scaling/late arrivals?** Append events with a watermark/correction window, partition and rebuild affected cohorts. Current full snapshots favor correctness and simplicity.
11. **Production changes?** Restricted roles, secret stores, CDC, environment isolation, atomic reporting publication and calibration/drift monitoring.
12. **Amplitude/Mixpanel similarity?** Local event taxonomy, activation, funnels and cohorts; no external integration.
13. **Synthetic limits?** Latent engagement produces noisy correlations, not real customer findings or production model evidence.
14. **Monitoring?** Airflow failures stop downstream work; structured task logs, audits, dbt failures and the quality extract identify the failed stage.
15. **Repeatability?** Fixed seed/horizon yields identical source checksums. Transactional replacement prevents duplicate sources/scores; timestamps change on rerun.

Use actual results and limitations from FINAL_VERIFICATION.md instead of hoped-for model performance.
