"""Independent raw, business and artifact checks; failed checks stop the pipeline."""

import json
from datetime import datetime, timezone

import joblib
import pandas as pd
from psycopg import sql

from platform_app.config import Settings
from platform_app.database import connect, query
from platform_app.generate import TABLE_COLUMNS


def validate_frame(frame: pd.DataFrame, key: str, required=(), categories=None, foreign_keys=None):
    if frame.empty or frame[key].isna().any() or frame[key].duplicated().any():
        raise ValueError(f"Empty data, duplicate or null key: {key}")
    for name in required:
        if frame[name].isna().any():
            raise ValueError(f"Null required column: {name}")
    for name, allowed in (categories or {}).items():
        if not frame[name].isin(allowed).all():
            raise ValueError(f"Invalid category: {name}")
    for name, allowed in (foreign_keys or {}).items():
        if not frame[name].dropna().isin(allowed).all():
            raise ValueError(f"Broken relationship: {name}")


def record_checks(checks: list[tuple]):
    with connect() as conn:
        for name, passed, observed in checks:
            conn.execute(
                "INSERT INTO reporting.data_quality VALUES(%s,%s,%s,now()) ON CONFLICT(check_name) DO UPDATE SET passed=excluded.passed,observed_value=excluded.observed_value,checked_at=excluded.checked_at",
                (name, bool(passed), str(observed)),
            )
    failures = [name for name, passed, _ in checks if not passed]
    if failures:
        raise ValueError(f"Data quality failed: {failures}")


def raw_checks(settings: Settings):
    checks = []
    manifest = json.loads((settings.generated / "manifest.json").read_text())
    with connect() as conn:
        for table in TABLE_COLUMNS:
            n = conn.execute(
                sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier("raw", table))
            ).fetchone()["n"]
            checks.append((f"raw_count_{table}", n == manifest["counts"][table], n))
        invalid = conn.execute(
            """SELECT count(*) AS n FROM raw.events e JOIN raw.users u USING(user_id)
             LEFT JOIN raw.features f USING(feature_id)
             WHERE e.event_at<u.signup_at OR e.product_id<>u.product_id
             OR (e.feature_id IS NOT NULL AND e.product_id<>f.product_id)
             OR e.event_at < %s OR e.event_at >= %s::date+interval '1 day' """,
            (settings.start, settings.end),
        ).fetchone()["n"]
        checks.append(("event_temporal_and_product_integrity", invalid == 0, invalid))
        complete = conn.execute("""SELECT count(*) AS n FROM raw.users u WHERE NOT EXISTS
             (SELECT 1 FROM raw.events e WHERE e.user_id=u.user_id AND e.event_type='signup')""").fetchone()[
            "n"
        ]
        checks.append(("all_users_have_signup", complete == 0, complete))
        missing = conn.execute(
            "SELECT count(*) AS n FROM raw.events WHERE user_id IS NULL OR event_at IS NULL OR session_id IS NULL OR event_type IS NULL"
        ).fetchone()["n"]
        checks.append(("required_event_fields_complete", missing == 0, missing))
        checks.append(("source_history_end", True, str(settings.end)))
        age = conn.execute(
            "SELECT extract(epoch FROM(now()-loaded_at))/3600 AS hours FROM control.run_config"
        ).fetchone()["hours"]
        checks.append(("ingestion_freshness_hours", 0 <= age < 24, round(float(age), 4)))
    record_checks(checks)
    return checks


def verify(settings: Settings):
    from platform_app.reporting import EXPORTS, export_quality

    checks = raw_checks(settings)
    expected_models = [p.stem for p in (settings.root / "dbt/models").rglob("*.sql")]
    observed = query(
        "SELECT table_name FROM information_schema.tables WHERE table_schema IN ('staging','intermediate','marts')"
    )
    observed_names = {r["table_name"] for r in observed}
    final = [("dbt_models_exist", set(expected_models) <= observed_names, len(observed_names))]
    counts = {}
    with connect() as conn:
        for schema in ("raw", "staging", "intermediate", "marts"):
            for row in conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema=%s ORDER BY table_name",
                (schema,),
            ):
                table = row["table_name"]
                n = conn.execute(
                    sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier(schema, table))
                ).fetchone()["n"]
                counts[f"{schema}.{table}"] = n
                final.append((f"nonempty_{schema}_{table}", n > 0, n))
        # Independent DAU and 30-day MAU verification against raw timestamps on final date.
        for product in range(1, 6):
            metrics = conn.execute(
                "SELECT dau, wau, mau FROM marts.mart_product_metrics WHERE metric_date=%s AND product_id=%s",
                (settings.end, product),
            ).fetchone()
            counts_activity = conn.execute(
                """SELECT
              count(distinct user_id) filter(where event_at>=%s::date) AS dau,
              count(distinct user_id) filter(where event_at>=%s::date-interval '6 days') AS wau,
              count(distinct user_id) AS mau FROM raw.events
              WHERE product_id=%s AND event_at>=%s::date-interval '29 days' AND event_at<%s::date+interval '1 day'
              AND event_type IN ('login','feature_used','search','report_created','export_completed','invite_sent','invite_accepted')""",
                (settings.end, settings.end, product, settings.end, settings.end),
            ).fetchone()
            final.append(
                (
                    f"active_user_reconciliation_product_{product}",
                    metrics == counts_activity,
                    str(counts_activity),
                )
            )
        revenue = conn.execute(
            "SELECT sum(amount) AS n FROM raw.transactions WHERE status='succeeded'"
        ).fetchone()["n"]
        mart_rev = conn.execute(
            "SELECT sum(revenue) AS n FROM marts.mart_product_metrics"
        ).fetchone()["n"]
        final.append(("revenue_reconciles_to_raw", revenue == mart_rev, str(revenue)))
        ml_count = conn.execute(
            "SELECT count(*) AS n FROM intermediate.int_churn_features WHERE cutoff_date=%s",
            (settings.end,),
        ).fetchone()["n"]
        final.append(
            (
                "score_population_reconciles",
                ml_count == counts["marts.mart_churn_predictions"],
                ml_count,
            )
        )
    for name in EXPORTS:
        path = settings.outputs / "bi" / f"{name}.csv"
        passed = path.exists() and path.stat().st_size > 0 and len(pd.read_csv(path)) > 0
        final.append((f"export_{name}", passed, path.name))
    ml_dir = settings.outputs / "ml"
    for name in (
        "churn_model.joblib",
        "evaluation.json",
        "feature_metadata.json",
        "predictions.csv",
        "coefficients.csv",
        "test_predictions.csv",
        "features.csv",
    ):
        path = ml_dir / name
        final.append((f"ml_artifact_{name}", path.exists() and path.stat().st_size > 0, name))
    evaluation = json.loads((ml_dir / "evaluation.json").read_text())
    final.append(("ml_evaluation_valid", 0 <= evaluation["roc_auc"] <= 1, evaluation["roc_auc"]))
    model = joblib.load(ml_dir / "churn_model.joblib")
    from platform_app.ml import FEATURES

    features = pd.read_csv(ml_dir / "features.csv")
    final.append(
        (
            "persisted_model_loads",
            model.predict_proba(features[FEATURES].head()).shape == (5, 2),
            "5 rows",
        )
    )
    dbt_results = json.loads((settings.root / "dbt/target/run_results.json").read_text())
    statuses = [r["status"] for r in dbt_results["results"]]
    test_results = [r for r in dbt_results["results"] if r["unique_id"].startswith("test.")]
    # docs generate may overwrite run_results; dbt_test_summary is captured before documentation.
    summary_path = settings.outputs / "verification" / "dbt_test_summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
    else:
        summary = {
            "passed": sum(r["status"] == "pass" for r in test_results),
            "failed": sum(r["status"] != "pass" for r in test_results),
        }
    final.append(("dbt_tests_passed", summary["passed"] > 0 and summary["failed"] == 0, summary))
    final.append(
        ("dbt_last_execution_ok", all(s in ("pass", "success") for s in statuses), len(statuses))
    )
    final.append(
        (
            "pipeline_status",
            all(passed for _, passed, _ in final),
            "success" if all(passed for _, passed, _ in final) else "failed",
        )
    )
    record_checks(final)
    export_quality(settings)
    result = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "row_counts": counts,
        "checks_passed": len(checks) + len(final),
        "checks_failed": 0,
        "dbt_tests": summary,
        "ml": evaluation,
        "latest_metrics": query(
            "SELECT * FROM marts.mart_product_metrics WHERE metric_date=%s ORDER BY product_id",
            (settings.end,),
        ),
    }
    target = settings.outputs / "verification" / "pipeline_verification.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return result
