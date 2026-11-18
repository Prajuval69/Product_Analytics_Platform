"""Build the public read-only demo from verified aggregate synthetic results."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "outputs"
bi = source / "bi"
target = ROOT / "website"
target.mkdir(exist_ok=True)
verification = json.loads((source / "verification/pipeline_verification.json").read_text())
metrics = pd.read_csv(bi / "executive_kpis.csv")
funnel = (
    pd.read_csv(bi / "product_funnel.csv")
    .groupby(["product_id", "step_number", "step_name"], as_index=False)[
        ["entrants", "users_at_step"]
    ]
    .sum()
)
retention = (
    pd.read_csv(bi / "retention_cohorts.csv")
    .groupby(["product_id", "cohort_month", "offset_days"], as_index=False)[
        ["eligible_users", "retained_users"]
    ]
    .sum()
)
features = (
    pd.read_csv(bi / "feature_adoption.csv")
    .groupby(["product_id", "feature_id", "feature_name"], as_index=False)[
        ["eligible_active_users", "adopted_users", "use_count"]
    ]
    .sum()
)
health = pd.read_csv(bi / "churn_predictions.csv")
data = {
    "metrics": json.loads(metrics.to_json(orient="records")),
    "funnel": json.loads(funnel.to_json(orient="records")),
    "retention": json.loads(retention.to_json(orient="records")),
    "features": json.loads(features.to_json(orient="records")),
    "risk": health.risk_band.value_counts().to_dict(),
    "ml": verification["ml"],
    "verified_at": verification["verified_at"],
    "checks": verification["checks_passed"],
    "counts": verification["row_counts"],
}
(target / "data.json").write_text(
    json.dumps(data, separators=(",", ":"), allow_nan=False), encoding="utf-8"
)
print(f"Demo built: {len(metrics)} product/date rows; aggregate synthetic results only")
