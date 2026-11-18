"""Maintain documented grains and standard dbt constraints without external packages."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GRAINS = {
    "stg_users": ("user_id", "One row per registered user; immutable signup plan."),
    "stg_products": ("product_id", "One row per synthetic SaaS product."),
    "stg_features": ("feature_id", "One row per product-owned feature."),
    "stg_events": (
        "event_id",
        "One row per event; UTC event dates; activity classification is canonical.",
    ),
    "stg_subscriptions": (
        "subscription_id",
        "One row per subscription lifetime; at most one per user in this simulation.",
    ),
    "stg_transactions": (
        "transaction_id",
        "One row per invoice attempt; only succeeded attempts recognize revenue.",
    ),
    "stg_support_tickets": ("ticket_id", "One row per support interaction, possibly unresolved."),
    "int_user_daily_activity": (None, "One row per user, product and UTC active date."),
    "int_user_feature_usage": (
        None,
        "One row per user, feature, calendar month and immutable signup plan.",
    ),
    "int_user_sessions": (
        "session_id",
        "One row per explicit source session, including non-active lifecycle sessions.",
    ),
    "int_user_funnel": (
        "user_id",
        "One row per user with ordered 30-day funnel timestamps and 7-day activation timestamp.",
    ),
    "int_user_revenue": ("user_id", "One row per user with successful lifetime billing revenue."),
    "int_customer_health": (
        "user_id",
        "One row per user, as of the configured history end; descriptive current-state snapshot.",
    ),
    "int_churn_features": (
        None,
        "One row per eligible user and cutoff date. Predictors observe trailing 30 days. The label observes only future 30 days; current scoring labels are null.",
    ),
    "dim_user": (
        "user_key",
        "One row per user; type 1 dimension with namespace-prefixed MD5 surrogate key.",
    ),
    "dim_product": (
        "product_key",
        "One row per product with stable namespace-prefixed surrogate key.",
    ),
    "dim_feature": (
        "feature_key",
        "One row per feature with stable namespace-prefixed surrogate key.",
    ),
    "dim_date": ("date_key", "One row per UTC calendar date in the configured source horizon."),
    "fct_events": (
        "event_key",
        "One row per event; nullable feature key for events without a feature.",
    ),
    "fct_sessions": (
        "session_key",
        "One row per user session; duration measured first-to-last observed event.",
    ),
    "fct_transactions": (
        "transaction_key",
        "One row per invoice attempt; failed attempts have zero recognized revenue.",
    ),
    "fct_subscriptions": (
        "subscription_key",
        "One row per subscription lifetime with start, cancellation and monthly list price.",
    ),
    "fct_support_tickets": (
        "ticket_key",
        "One row per support ticket with nullable resolution duration.",
    ),
    "mart_product_metrics": (
        "metric_key",
        "One row per date and product, including dates with zero activity. Rates retain denominators.",
    ),
    "mart_funnel_analysis": (
        "funnel_key",
        "One row per product, channel, country, plan and ordered funnel step. Only 30-day mature signups enter.",
    ),
    "mart_retention_cohorts": (
        "cohort_key",
        "One row per signup month, product, channel and exact-day offset. Immature users excluded from rate denominator.",
    ),
    "mart_feature_adoption": (
        "adoption_key",
        "One row per month, feature and plan; denominator is distinct active users of its product and plan in that month.",
    ),
    "mart_customer_health": (
        "user_key",
        "One row per user descriptive snapshot; use for customer segmentation, not predictive features.",
    ),
    "mart_churn_predictions": (
        "user_id",
        "One row per currently eligible scored user; live view over atomic ML output. Not all registered users are eligible.",
    ),
}


def column(name, description, tests=None):
    result = {"name": name, "description": description}
    if tests:
        result["tests"] = tests
    return result


def relationship(model, field):
    return {"relationships": {"to": "ref('%s')" % model, "field": field}}


def write_schema():
    models = []
    for name, (key, grain) in GRAINS.items():
        columns = []
        if key:
            columns.append(
                column(key, "Unique key at the documented grain.", ["not_null", "unique"])
            )
        if (
            name != "stg_users"
            and name.startswith(("stg_", "int_"))
            and name not in ("stg_products", "stg_features")
        ):
            columns.append(
                column(
                    "user_id",
                    "Registered user natural key.",
                    ["not_null", relationship("stg_users", "user_id")],
                )
            )
        if name not in ("stg_products", "dim_date") and not name.startswith("mart_"):
            columns.append(
                column(
                    "product_id",
                    "Product owning this row.",
                    ["not_null", relationship("stg_products", "product_id")],
                )
            )
        if name.startswith("fct_"):
            columns += [
                column(
                    "user_key",
                    "User surrogate key.",
                    ["not_null", relationship("dim_user", "user_key")],
                ),
                column(
                    "product_key",
                    "Product surrogate key.",
                    ["not_null", relationship("dim_product", "product_key")],
                ),
                column(
                    "date_key",
                    "UTC date of occurrence or subscription start.",
                    ["not_null", relationship("dim_date", "date_key")],
                ),
            ]
        if name == "fct_events":
            columns.append(
                column(
                    "feature_key",
                    "Nullable when event has no feature.",
                    [relationship("dim_feature", "feature_key")],
                )
            )
        if name == "stg_events":
            columns += [
                column(
                    "feature_id",
                    "Optional feature natural key.",
                    [relationship("stg_features", "feature_id")],
                ),
                column("event_at", "UTC source timestamp.", ["not_null"]),
                column(
                    "event_type",
                    "Source event taxonomy.",
                    [
                        "not_null",
                        {
                            "accepted_values": {
                                "values": [
                                    "signup",
                                    "login",
                                    "onboarding_started",
                                    "onboarding_completed",
                                    "feature_viewed",
                                    "feature_used",
                                    "search",
                                    "report_created",
                                    "export_completed",
                                    "invite_sent",
                                    "invite_accepted",
                                    "upgrade_started",
                                    "purchase_completed",
                                    "support_opened",
                                    "churn_signal",
                                ]
                            }
                        },
                    ],
                ),
                column(
                    "device",
                    "Client platform.",
                    [{"accepted_values": {"values": ["web", "ios", "android"]}}],
                ),
            ]
        if name == "stg_users":
            columns += [
                column("signup_at", "Immutable registration timestamp.", ["not_null"]),
                column(
                    "plan",
                    "Immutable signup plan.",
                    [{"accepted_values": {"values": ["free", "starter", "pro", "enterprise"]}}],
                ),
                column(
                    "acquisition_channel",
                    "Signup attribution.",
                    [
                        {
                            "accepted_values": {
                                "values": [
                                    "organic",
                                    "paid_search",
                                    "referral",
                                    "social",
                                    "partner",
                                ]
                            }
                        }
                    ],
                ),
            ]
        if name == "stg_transactions":
            columns += [
                column(
                    "subscription_id",
                    "Billed subscription.",
                    ["not_null", relationship("stg_subscriptions", "subscription_id")],
                ),
                column(
                    "status",
                    "Invoice result.",
                    [{"accepted_values": {"values": ["succeeded", "failed"]}}],
                ),
            ]
        if name == "stg_subscriptions":
            columns += [
                column(
                    "status",
                    "Current lifetime status.",
                    [{"accepted_values": {"values": ["active", "cancelled"]}}],
                )
            ]
        if name == "stg_support_tickets":
            columns += [
                column(
                    "priority",
                    "Support priority.",
                    [{"accepted_values": {"values": ["low", "medium", "high"]}}],
                )
            ]
        if name == "int_churn_features":
            columns += [
                column("cutoff_date", "Inclusive last observation date.", ["not_null"]),
                column(
                    "churned",
                    "Future outcome; must never enter the predictor list.",
                    [{"accepted_values": {"values": [0, 1], "quote": False}}],
                ),
                column("days_since_last_activity", "Recency at cutoff.", ["not_null"]),
            ]
        if name == "mart_churn_predictions":
            columns += [
                column("churn_probability", "Probability of future 30-day churn.", ["not_null"]),
                column(
                    "risk_band",
                    "Fixed probability bands.",
                    [{"accepted_values": {"values": ["low", "medium", "high"]}}],
                ),
                column("scoring_date", "Observation cutoff used for scoring.", ["not_null"]),
            ]
        merged = {}
        for entry in columns:
            if entry["name"] not in merged:
                merged[entry["name"]] = entry
            else:
                existing = merged[entry["name"]].setdefault("tests", [])
                for test in entry.get("tests", []):
                    if test not in existing:
                        existing.append(test)
        models.append({"name": name, "description": grain, "columns": list(merged.values())})
    (ROOT / "dbt/models/schema.yml").write_text(
        yaml.safe_dump({"version": 2, "models": models}, sort_keys=False), encoding="utf-8"
    )
    sources = [
        {"name": "raw", "schema": "raw", "tables": []},
        {"name": "control", "schema": "control", "tables": []},
    ]
    keys = {
        "users": "user_id",
        "products": "product_id",
        "features": "feature_id",
        "events": "event_id",
        "subscriptions": "subscription_id",
        "transactions": "transaction_id",
        "support_tickets": "ticket_id",
    }
    for table, key in keys.items():
        sources[0]["tables"].append(
            {
                "name": table,
                "description": "Synthetic source; atomic snapshot COPY replacement.",
                "columns": [column(key, "Source primary key.", ["not_null", "unique"])],
            }
        )
    sources[1]["tables"] = [
        {
            "name": "run_config",
            "description": "One active source horizon and seed; loaded_at is operational ingestion freshness.",
        },
        {
            "name": "ml_predictions",
            "description": "Atomically replaced scoring output, populated after dbt transforms.",
        },
    ]
    (ROOT / "dbt/models/sources.yml").write_text(
        yaml.safe_dump({"version": 2, "sources": sources}, sort_keys=False), encoding="utf-8"
    )


if __name__ == "__main__":
    write_schema()
