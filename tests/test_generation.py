import json
from dataclasses import replace
from datetime import date

import pandas as pd
import pytest

from platform_app.config import Settings
from platform_app.generate import EVENT_TYPES, TABLE_COLUMNS, generate
from platform_app.quality import validate_frame


def test_seed_reproducibility(sample, tmp_path):
    config, manifest = sample
    second = generate(replace(config, root=tmp_path))
    assert manifest == second


def test_different_seed_changes_sources(sample, tmp_path):
    config, manifest = sample
    second = generate(replace(config, root=tmp_path, seed=config.seed + 1))
    assert manifest["sha256"]["events"] != second["sha256"]["events"]


@pytest.mark.parametrize("table", TABLE_COLUMNS)
def test_generated_grains_and_counts(sample, table):
    config, manifest = sample
    frame = pd.read_csv(config.generated / f"{table}.csv")
    assert list(frame.columns) == TABLE_COLUMNS[table]
    assert len(frame) == manifest["counts"][table] > 0
    validate_frame(frame, TABLE_COLUMNS[table][0])


def test_generated_relationships_time_and_taxonomy(sample):
    config, _ = sample
    users = pd.read_csv(config.generated / "users.csv")
    events = pd.read_csv(config.generated / "events.csv")
    features = pd.read_csv(config.generated / "features.csv")
    validate_frame(
        events,
        "event_id",
        required=["user_id", "session_id", "event_at"],
        categories={"event_type": EVENT_TYPES},
        foreign_keys={"user_id": users.user_id, "feature_id": features.feature_id},
    )
    joined = events.merge(
        users[["user_id", "signup_at", "product_id"]], on="user_id", suffixes=("", "_user")
    )
    assert (pd.to_datetime(joined.event_at) >= pd.to_datetime(joined.signup_at)).all()
    assert (joined.product_id == joined.product_id_user).all()
    assert pd.to_datetime(joined.event_at).max().date() <= config.end
    assert set(events[events.event_type == "signup"].user_id) == set(users.user_id)
    assert events.groupby("session_id").user_id.nunique().max() == 1
    assert all(json.loads(p)["source"] == "synthetic" for p in events.properties)


@pytest.mark.parametrize(
    "values", [{"users": 9}, {"start": date(2025, 9, 1)}, {"end": date(2024, 1, 1)}]
)
def test_invalid_configuration_rejected(values):
    with pytest.raises(ValueError):
        Settings(**values)


def test_subscription_transactions_respect_lifecycle(sample):
    config, _ = sample
    tx = pd.read_csv(config.generated / "transactions.csv")
    sub = pd.read_csv(config.generated / "subscriptions.csv")
    joined = tx.merge(sub, on="subscription_id", suffixes=("", "_sub"))
    assert (joined.user_id == joined.user_id_sub).all()
    assert (joined.product_id == joined.product_id_sub).all()
    assert (pd.to_datetime(joined.transaction_at) >= pd.to_datetime(joined.started_at)).all()
    cancelled = joined[joined.cancelled_at.notna()]
    assert (pd.to_datetime(cancelled.transaction_at) < pd.to_datetime(cancelled.cancelled_at)).all()
    assert (tx.amount > 0).all()
