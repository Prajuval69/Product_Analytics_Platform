import json
from datetime import timedelta

import numpy as np
import pandas as pd
import psycopg
import pytest
from psycopg import sql

from platform_app.config import ROOT, Settings
from platform_app.database import connect, query
from platform_app.generate import ACTIVE_EVENTS, TABLE_COLUMNS
from platform_app.ml import FEATURES
from platform_app.quality import verify
from platform_app.reporting import EXPORTS

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("table", TABLE_COLUMNS)
def test_raw_counts_and_fact_grains(table):
    manifest = json.loads((ROOT / "data/generated/manifest.json").read_text())
    with connect() as conn:
        n = conn.execute(
            sql.SQL("SELECT count(*) AS n FROM {}").format(sql.Identifier("raw", table))
        ).fetchone()["n"]
    assert n == manifest["counts"][table]
    mapping = {
        "events": "fct_events",
        "transactions": "fct_transactions",
        "subscriptions": "fct_subscriptions",
        "support_tickets": "fct_support_tickets",
    }
    if table in mapping:
        assert query(f"SELECT count(*) AS n FROM marts.{mapping[table]}")[0]["n"] == n


@pytest.mark.parametrize("case", ["duplicate", "invalid_plan", "orphan"])
def test_raw_constraints_and_rollback(case):
    before = query("SELECT count(*) AS n FROM raw.users")[0]["n"]
    with pytest.raises(psycopg.IntegrityError):
        with connect() as conn:
            if case == "duplicate":
                conn.execute("INSERT INTO raw.users SELECT * FROM raw.users WHERE user_id=1")
            else:
                conn.execute(
                    "INSERT INTO raw.users VALUES(999999,%s,'2025-01-01','organic','US',%s,'web')",
                    (
                        999 if case == "orphan" else 1,
                        "invalid" if case == "invalid_plan" else "free",
                    ),
                )
    assert query("SELECT count(*) AS n FROM raw.users")[0]["n"] == before


@pytest.fixture(scope="module")
def reference_data():
    events = pd.DataFrame(
        query("SELECT user_id,event_at,event_type,product_id FROM raw.events WHERE product_id=1")
    )
    events["date"] = pd.to_datetime(events.event_at, utc=True).dt.date
    users = pd.DataFrame(
        query("SELECT user_id,signup_at,product_id FROM raw.users WHERE product_id=1")
    )
    users["date"] = pd.to_datetime(users.signup_at, utc=True).dt.date
    return events, users


@pytest.mark.parametrize("offset", [0, 6, 29, 89, 272])
def test_active_metrics_against_python_sets(reference_data, offset):
    config = Settings.from_env()
    day = config.start + timedelta(days=min(offset, (config.end - config.start).days))
    events, _ = reference_data
    active = events[events.event_type.isin(ACTIVE_EVENTS)]
    expected = {
        name: len(
            set(active[(active.date >= day - timedelta(days=n - 1)) & (active.date <= day)].user_id)
        )
        for name, n in [("dau", 1), ("wau", 7), ("mau", 30)]
    }
    row = query(
        "SELECT dau,wau,mau FROM marts.mart_product_metrics WHERE metric_date=%s AND product_id=1",
        (day,),
    )[0]
    assert row == expected


def test_activation_against_raw_python(reference_data):
    config = Settings.from_env()
    events, users = reference_data
    eligible = users[users.date <= config.end - timedelta(days=7)]
    uses = events[events.event_type == "feature_used"].merge(
        eligible, on="user_id", suffixes=("", "_user")
    )
    uses = uses[
        (uses.event_at >= uses.signup_at) & (uses.event_at < uses.signup_at + pd.Timedelta(days=7))
    ]
    metric = query(
        "SELECT activation_eligible,activated_users FROM marts.mart_product_metrics WHERE product_id=1 AND metric_date=%s",
        (config.end,),
    )[0]
    assert metric == {
        "activation_eligible": len(eligible),
        "activated_users": uses.user_id.nunique(),
    }


@pytest.mark.parametrize("offset", [1, 7, 30])
def test_retention_against_python_join(reference_data, offset):
    config = Settings.from_env()
    events, users = reference_data
    eligible = users[users.date + timedelta(days=offset) <= config.end]
    active = events[events.event_type.isin(ACTIVE_EVENTS)][["user_id", "date"]].drop_duplicates()
    joined = eligible.merge(active, on="user_id", suffixes=("_signup", "_event"))
    retained = joined[
        joined.date_event == joined.date_signup + timedelta(days=offset)
    ].user_id.nunique()
    row = query(
        "SELECT sum(eligible_users) AS eligible,sum(retained_users) AS retained FROM marts.mart_retention_cohorts WHERE product_id=1 AND offset_days=%s",
        (offset,),
    )[0]
    assert int(row["eligible"]) == len(eligible) and int(row["retained"]) == retained


def test_churn_label_matches_reporting_definition():
    config = Settings.from_env()
    cutoff = config.end - timedelta(days=30)
    labels = query(
        "SELECT product_id,count(*) AS eligible,sum(churned) AS churned FROM intermediate.int_churn_features WHERE cutoff_date=%s GROUP BY product_id ORDER BY product_id",
        (cutoff,),
    )
    mart = query(
        "SELECT product_id,churn_eligible AS eligible,churned_users AS churned FROM marts.mart_product_metrics WHERE metric_date=%s ORDER BY product_id",
        (config.end,),
    )
    assert labels == mart


@pytest.mark.parametrize("name", EXPORTS)
def test_bi_exports_are_nonempty(name):
    assert len(pd.read_csv(ROOT / "outputs/bi" / f"{name}.csv")) > 0


def test_ml_scoring_artifacts_consistent():
    import joblib

    config = Settings.from_env()
    folder = ROOT / "outputs/ml"
    frame = pd.read_csv(folder / "features.csv")
    latest = frame[frame.cutoff_date == str(config.end)]
    assert latest.churned.isna().all()
    scores = pd.read_csv(folder / "predictions.csv")
    expected = joblib.load(folder / "churn_model.joblib").predict_proba(latest[FEATURES])[:, 1]
    np.testing.assert_allclose(expected, scores.churn_probability)
    assert set(scores.user_id) == set(latest.user_id)
    assert query("SELECT count(*) AS n FROM marts.mart_churn_predictions")[0]["n"] == len(scores)


def test_future_source_changes_do_not_change_asof_predictors():
    """Inject post-cutoff revenue/events/tickets in a rolled-back transaction."""
    compiled = (
        ROOT / "dbt/target/compiled/product_analytics/models/intermediate/int_churn_features.sql"
    ).read_text()
    with connect() as conn:
        selected = conn.execute(
            "SELECT user_id,product_id,cutoff_date FROM intermediate.int_churn_features ORDER BY cutoff_date,user_id LIMIT 1"
        ).fetchone()
        statement = sql.SQL(
            "SELECT {} FROM ({}) snapshot WHERE user_id=%s AND cutoff_date=%s"
        ).format(sql.SQL(",").join(map(sql.Identifier, FEATURES)), sql.SQL(compiled))
        params = (selected["user_id"], selected["cutoff_date"])
        before = conn.execute(statement, params).fetchone()
        future = selected["cutoff_date"] + timedelta(days=5)
        conn.execute(
            "UPDATE raw.transactions SET amount=amount+1000 WHERE user_id=%s AND transaction_at>=%s::date+interval '1 day'",
            params,
        )
        conn.execute(
            "INSERT INTO raw.support_tickets VALUES(999998,%s,%s,%s,NULL,'high','bug')",
            (selected["user_id"], selected["product_id"], future),
        )
        conn.execute(
            "INSERT INTO raw.events VALUES(9999999,%s,%s,%s,'leakage-regression',%s,'feature_used','web','{}')",
            (
                selected["user_id"],
                selected["product_id"],
                (selected["product_id"] - 1) * 3 + 1,
                future,
            ),
        )
        after = conn.execute(statement, params).fetchone()
        assert before == after
        conn.rollback()


def test_complete_pipeline_verification():
    result = verify(Settings.from_env())
    assert result["checks_failed"] == 0 and result["checks_passed"] >= 70
