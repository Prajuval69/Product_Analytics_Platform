"""Flat reporting extracts and dimensions for a Power BI semantic model."""

import json

import pandas as pd

from platform_app.config import Settings
from platform_app.database import query

EXPORTS = {
    "executive_kpis": "SELECT m.*,p.product_name FROM marts.mart_product_metrics m JOIN marts.dim_product p USING(product_id) ORDER BY metric_date,product_id",
    "product_funnel": "SELECT f.*,p.product_name FROM marts.mart_funnel_analysis f JOIN marts.dim_product p USING(product_id) ORDER BY product_id,acquisition_channel,country,plan,step_number",
    "retention_cohorts": "SELECT f.*,p.product_name FROM marts.mart_retention_cohorts f JOIN marts.dim_product p USING(product_id) ORDER BY cohort_month,product_id,acquisition_channel,offset_days",
    "feature_adoption": "SELECT f.*,p.product_name FROM marts.mart_feature_adoption f JOIN marts.dim_product p USING(product_id) ORDER BY usage_month,product_id,feature_id,plan",
    "customer_health": "SELECT h.*,p.churn_probability,p.risk_band,p.scoring_date FROM marts.mart_customer_health h LEFT JOIN marts.mart_churn_predictions p USING(user_id) ORDER BY h.user_id",
    "churn_predictions": "SELECT * FROM marts.mart_churn_predictions ORDER BY user_id",
    "revenue_subscriptions": """SELECT t.transaction_id,t.subscription_id,t.user_id,t.product_id,t.transaction_date,t.amount,t.recognized_revenue,t.status,
         u.plan,u.acquisition_channel,u.country,s.monthly_price,s.started_at,s.cancelled_at,p.product_name
         FROM marts.fct_transactions t JOIN marts.dim_user u USING(user_id)
         JOIN marts.fct_subscriptions s USING(subscription_id) JOIN marts.dim_product p ON p.product_id=t.product_id ORDER BY t.transaction_id""",
    "data_quality": "SELECT * FROM reporting.data_quality ORDER BY check_name",
    "dim_date": "SELECT * FROM marts.dim_date ORDER BY date_day",
    "dim_product": "SELECT * FROM marts.dim_product ORDER BY product_id",
    "dim_user": "SELECT * FROM marts.dim_user ORDER BY user_id",
    "dim_feature": "SELECT * FROM marts.dim_feature ORDER BY feature_id",
    "subscriptions": "SELECT * FROM marts.fct_subscriptions ORDER BY subscription_id",
}


def export_quality(settings: Settings):
    folder = settings.outputs / "bi"
    folder.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(query(EXPORTS["data_quality"]))
    frame.to_csv(folder / "data_quality.csv", index=False)
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest["data_quality"] = {"rows": len(frame), "columns": frame.columns.tolist()}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def export(settings: Settings):
    folder = settings.outputs / "bi"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, statement in EXPORTS.items():
        frame = pd.DataFrame(query(statement))
        if frame.empty:
            raise ValueError(f"Empty reporting export: {name}")
        target = folder / f"{name}.csv"
        temporary = target.with_suffix(".tmp")
        frame.to_csv(temporary, index=False)
        temporary.replace(target)
        manifest[name] = {"rows": len(frame), "columns": frame.columns.tolist()}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
