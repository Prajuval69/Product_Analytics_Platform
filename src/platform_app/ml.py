"""Logistic regression with purged temporal windows and an explicit feature allowlist."""

import hashlib
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from platform_app.config import Settings
from platform_app.database import connect, query

NUMERIC_FEATURES = [
    "tenure_days",
    "sessions_30d",
    "active_days_30d",
    "event_count_30d",
    "days_since_last_activity",
    "feature_diversity",
    "key_feature_uses",
    "revenue_30d",
    "support_tickets_30d",
    "subscription_tenure_days",
]
CATEGORICAL_FEATURES = ["plan"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def feature_dataset(settings: Settings) -> Path:
    frame = pd.DataFrame(
        query("SELECT * FROM intermediate.int_churn_features ORDER BY cutoff_date,user_id")
    )
    if frame.empty or frame[FEATURES].isna().any().any():
        raise ValueError("ML features empty or incomplete")
    target = settings.outputs / "ml" / "features.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False)
    return target


def temporal_split(frame: pd.DataFrame):
    labeled = frame[frame.churned.notna()].copy()
    cutoffs = sorted(labeled.cutoff_date.unique())
    if len(cutoffs) != 3:
        raise ValueError("Three mature temporal snapshots required")
    train, validation, test = [labeled[labeled.cutoff_date == c].copy() for c in cutoffs]
    for part in (train, validation, test):
        if len(part) < 20 or part.churned.nunique() != 2:
            raise ValueError(
                "Each temporal split needs 20+ examples and both classes; increase users/history"
            )
    dates = pd.to_datetime(cutoffs)
    if any((dates[i + 1] - dates[i]).days < 60 for i in range(2)):
        raise ValueError("Observation and outcome windows must be disjoint across snapshots")
    return train, validation, test


def make_model(seed: int) -> Pipeline:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    preprocess = ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [
            ("preprocess", preprocess),
            (
                "classifier",
                LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed),
            ),
        ]
    )


def risk_bands(probabilities):
    return np.where(
        np.asarray(probabilities) >= 0.7,
        "high",
        np.where(np.asarray(probabilities) >= 0.3, "medium", "low"),
    )


def evaluate(labels, probabilities, threshold: float) -> dict:
    predictions = np.asarray(probabilities) >= threshold
    return {
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
    }


def train(settings: Settings) -> dict:
    path = feature_dataset(settings)
    frame = pd.read_csv(path)
    train_frame, validation, test = temporal_split(frame)
    model = make_model(settings.seed)
    model.fit(train_frame[FEATURES], train_frame.churned.astype(int))
    validation_prob = model.predict_proba(validation[FEATURES])[:, 1]
    candidates = np.arange(0.2, 0.81, 0.05)
    threshold = float(
        max(
            candidates,
            key=lambda t: f1_score(validation.churned, validation_prob >= t, zero_division=0),
        )
    )
    probabilities = model.predict_proba(test[FEATURES])[:, 1]
    result = evaluate(test.churned.astype(int), probabilities, threshold)
    result.update(
        {
            "model": "LogisticRegression",
            "threshold": threshold,
            "class_weight": "balanced",
            "train_rows": len(train_frame),
            "validation_rows": len(validation),
            "test_rows": len(test),
            "train_cutoff": str(train_frame.cutoff_date.iloc[0]),
            "validation_cutoff": str(validation.cutoff_date.iloc[0]),
            "test_cutoff": str(test.cutoff_date.iloc[0]),
            "test_prevalence": float(test.churned.mean()),
            "validation": evaluate(validation.churned, validation_prob, threshold),
            "constant_majority_baseline": {
                "accuracy": float(max(test.churned.mean(), 1 - test.churned.mean())),
                "roc_auc": 0.5,
            },
            "synthetic_data_only": True,
        }
    )
    # Keep the evaluated model for scoring; no silent refit on the held-out test set.
    artifact_dir = settings.outputs / "ml"
    model_tmp = artifact_dir / "model.tmp"
    joblib.dump(model, model_tmp)
    model_path = artifact_dir / "churn_model.joblib"
    os.replace(model_tmp, model_path)
    version = hashlib.sha256(model_path.read_bytes()).hexdigest()[:12]
    current = frame[frame.cutoff_date == str(settings.end)].copy()
    if current.empty or current.churned.notna().any():
        raise ValueError("Current scoring population must exist without future labels")
    current["churn_probability"] = model.predict_proba(current[FEATURES])[:, 1]
    current["risk_band"] = risk_bands(current.churn_probability)
    current["scoring_date"] = str(settings.end)
    current["model_version"] = version
    scores = current[["user_id", "churn_probability", "risk_band", "scoring_date", "model_version"]]
    with connect() as conn:
        conn.execute("DELETE FROM control.ml_predictions")
        with conn.cursor().copy("COPY control.ml_predictions FROM STDIN") as copy:
            for row in scores.itertuples(index=False, name=None):
                copy.write_row(row)
    scores.to_csv(artifact_dir / "predictions.csv", index=False)
    result["scored_users"] = len(scores)
    result["model_version"] = version
    (artifact_dir / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    metadata = {
        "features": FEATURES,
        "observation_days": 30,
        "prediction_horizon_days": 30,
        "scoring_date": str(settings.end),
        "excluded": [
            "user_id",
            "product_id",
            "cutoff_date",
            "churned",
            "future_activity",
            "cancelled_at",
        ],
        "trained_cutoff": result["train_cutoff"],
        "model_version": version,
    }
    (artifact_dir / "feature_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    names = model.named_steps["preprocess"].get_feature_names_out()
    pd.DataFrame(
        {"feature": names, "standardized_coefficient": model.named_steps["classifier"].coef_[0]}
    ).to_csv(artifact_dir / "coefficients.csv", index=False)
    pd.DataFrame(
        {
            "user_id": test.user_id,
            "cutoff_date": test.cutoff_date,
            "label": test.churned,
            "probability": probabilities,
        }
    ).to_csv(artifact_dir / "test_predictions.csv", index=False)
    return result
