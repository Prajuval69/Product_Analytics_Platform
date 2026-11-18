import joblib
import numpy as np
import pandas as pd
import pytest

from platform_app.ml import (
    FEATURES,
    NUMERIC_FEATURES,
    evaluate,
    make_model,
    risk_bands,
    temporal_split,
)


@pytest.fixture
def ml_frame():
    rng = np.random.default_rng(12)
    frame = pd.DataFrame({name: rng.uniform(0, 10, 120) for name in NUMERIC_FEATURES})
    frame["plan"] = np.tile(["free", "starter", "pro", "enterprise"], 30)
    frame["churned"] = np.tile([0, 1], 60).astype(float)
    frame["cutoff_date"] = np.repeat(["2025-05-03", "2025-07-02", "2025-08-31", "2025-09-30"], 30)
    frame.loc[90:, "churned"] = np.nan
    frame["user_id"] = np.tile(np.arange(30), 4)
    return frame


def test_temporal_split_and_exclusion(ml_frame):
    train, validation, test = temporal_split(ml_frame)
    assert [len(x) for x in [train, validation, test]] == [30, 30, 30]
    assert train.cutoff_date.max() < validation.cutoff_date.min() < test.cutoff_date.min()
    assert not {"user_id", "cutoff_date", "churned", "cancelled_at", "future_active_days"} & set(
        FEATURES
    )


@pytest.mark.parametrize("invalid", ["missing_snapshot", "single_class", "overlap", "small_split"])
def test_invalid_split_rejected(ml_frame, invalid):
    if invalid == "missing_snapshot":
        ml_frame = ml_frame[ml_frame.cutoff_date != "2025-07-02"]
    elif invalid == "single_class":
        ml_frame.loc[ml_frame.cutoff_date == "2025-07-02", "churned"] = 0
    elif invalid == "overlap":
        ml_frame.loc[ml_frame.cutoff_date == "2025-07-02", "cutoff_date"] = "2025-05-15"
    elif invalid == "small_split":
        ml_frame = ml_frame.iloc[20:]
    with pytest.raises(ValueError):
        temporal_split(ml_frame)


def test_model_persistence_and_unknown_category(ml_frame, tmp_path):
    train, _, test = temporal_split(ml_frame)
    model = make_model(42).fit(train[FEATURES], train.churned)
    before = model.predict_proba(test[FEATURES])
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    np.testing.assert_allclose(before, joblib.load(path).predict_proba(test[FEATURES]))
    test.loc[:, "plan"] = "new_plan"
    assert np.isfinite(model.predict_proba(test[FEATURES])).all()


@pytest.mark.parametrize(
    "probability,expected",
    [(0, "low"), (0.299, "low"), (0.3, "medium"), (0.699, "medium"), (0.7, "high"), (1, "high")],
)
def test_risk_band_boundaries(probability, expected):
    assert risk_bands([probability])[0] == expected


def test_evaluation_known_answer():
    result = evaluate([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], 0.5)
    assert result["roc_auc"] == result["precision"] == result["recall"] == result["f1"] == 1
    assert result["confusion_matrix"] == [[2, 0], [0, 2]]
