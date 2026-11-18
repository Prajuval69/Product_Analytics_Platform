"""Seeded SaaS simulation with latent engagement and noisy lifecycle transitions."""

import csv
import hashlib
import json
from datetime import datetime, time, timedelta, timezone

import numpy as np

from platform_app.config import Settings

TABLE_COLUMNS = {
    "products": ["product_id", "product_name", "category"],
    "features": ["feature_id", "product_id", "feature_name", "is_key_feature"],
    "users": [
        "user_id",
        "product_id",
        "signup_at",
        "acquisition_channel",
        "country",
        "plan",
        "device",
    ],
    "events": [
        "event_id",
        "user_id",
        "product_id",
        "feature_id",
        "session_id",
        "event_at",
        "event_type",
        "device",
        "properties",
    ],
    "subscriptions": [
        "subscription_id",
        "user_id",
        "product_id",
        "plan",
        "started_at",
        "cancelled_at",
        "monthly_price",
        "status",
    ],
    "transactions": [
        "transaction_id",
        "subscription_id",
        "user_id",
        "product_id",
        "transaction_at",
        "amount",
        "currency",
        "status",
    ],
    "support_tickets": [
        "ticket_id",
        "user_id",
        "product_id",
        "opened_at",
        "resolved_at",
        "priority",
        "category",
    ],
}
ACTIVE_EVENTS = (
    "login",
    "feature_used",
    "search",
    "report_created",
    "export_completed",
    "invite_sent",
    "invite_accepted",
)
EVENT_TYPES = (
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
)


def generate(settings: Settings) -> dict:
    folder = settings.generated
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(settings.seed)
    files, writers, counts = {}, {}, dict.fromkeys(TABLE_COLUMNS, 0)
    for table, columns in TABLE_COLUMNS.items():
        files[table] = (folder / f"{table}.csv").open("w", newline="", encoding="utf-8")
        writers[table] = csv.writer(files[table])
        writers[table].writerow(columns)

    def add(table, values):
        writers[table].writerow([v.isoformat() if isinstance(v, datetime) else v for v in values])
        counts[table] += 1

    def event(user, product, session, timestamp, kind, device, feature=None):
        add(
            "events",
            [
                counts["events"] + 1,
                user,
                product,
                feature,
                session,
                timestamp,
                kind,
                device,
                json.dumps({"source": "synthetic", "schema_version": 1}, separators=(",", ":")),
            ],
        )

    origin = datetime.combine(settings.start, time(), tzinfo=timezone.utc)
    end = datetime.combine(settings.end + timedelta(days=1), time(), tzinfo=timezone.utc)
    days = (settings.end - settings.start).days + 1
    try:
        for product, name in enumerate(
            ["Insight Studio", "Flow Manager", "Team Workspace", "Data Explorer", "Report Cloud"], 1
        ):
            add("products", [product, name, "SaaS"])
            for j, feature in enumerate(["Analysis", "Collaboration", "Automation"]):
                add("features", [(product - 1) * 3 + j + 1, product, f"{name} {feature}", j == 0])
        for user in range(1, settings.users + 1):
            product = int(rng.integers(1, 6))
            engagement = float(rng.beta(2, 3))
            signup_day = int(rng.integers(0, max(2, days - 90)))
            signup = origin + timedelta(days=signup_day, hours=int(rng.integers(6, 18)))
            device = str(rng.choice(["web", "ios", "android"], p=[0.65, 0.2, 0.15]))
            channel = str(
                rng.choice(
                    ["organic", "paid_search", "referral", "social", "partner"],
                    p=[0.35, 0.25, 0.2, 0.12, 0.08],
                )
            )
            country = str(
                rng.choice(["US", "GB", "IN", "DE", "CA", "AU"], p=[0.3, 0.15, 0.25, 0.1, 0.1, 0.1])
            )
            plan = str(
                rng.choice(
                    ["free", "starter", "pro", "enterprise"],
                    p=[
                        1 - (0.2 + 0.65 * engagement),
                        (0.2 + 0.65 * engagement) * 0.6,
                        (0.2 + 0.65 * engagement) * 0.3,
                        (0.2 + 0.65 * engagement) * 0.1,
                    ],
                )
            )
            add("users", [user, product, signup, channel, country, plan, device])
            signup_session = f"u{user}-signup"
            event(user, product, signup_session, signup, "signup", device)
            event(
                user,
                product,
                signup_session,
                signup + timedelta(minutes=2),
                "onboarding_started",
                device,
            )
            onboarded = rng.random() < 0.45 + 0.5 * engagement
            if onboarded:
                event(
                    user,
                    product,
                    signup_session,
                    signup + timedelta(minutes=8),
                    "onboarding_completed",
                    device,
                )
                if rng.random() < 0.45 + 0.5 * engagement:
                    event(
                        user,
                        product,
                        signup_session,
                        signup + timedelta(minutes=15),
                        "feature_used",
                        device,
                        (product - 1) * 3 + 1,
                    )
            # Latent disengagement is never stored in raw data or ML features.
            dropout = days
            if rng.random() < 0.7 - 0.55 * engagement:
                dropout = min(days, signup_day + int(rng.integers(35, max(36, days - signup_day))))
            activity_end = min(days, dropout)
            available = np.arange(signup_day + 1, activity_end)
            probabilities = (0.04 + 0.28 * engagement) * np.where(
                available >= dropout - 30, 0.3, 1.0
            )
            probabilities *= np.where((available + origin.weekday()) % 7 >= 5, 0.72, 1.0)
            active_days = available[rng.random(len(available)) < probabilities]
            for day in active_days:
                session = f"u{user}-d{day}"
                timestamp = origin + timedelta(days=int(day), hours=int(rng.integers(7, 22)))
                event(user, product, session, timestamp, "login", device)
                for step in range(int(rng.integers(3, 8))):
                    kind = str(
                        rng.choice(
                            [
                                "feature_viewed",
                                "feature_used",
                                "search",
                                "report_created",
                                "export_completed",
                                "invite_sent",
                                "invite_accepted",
                            ],
                            p=[0.15, 0.35, 0.18, 0.12, 0.1, 0.07, 0.03],
                        )
                    )
                    feature = (
                        (product - 1) * 3 + int(rng.choice([1, 2, 3], p=[0.55, 0.3, 0.15]))
                        if kind
                        in ("feature_viewed", "feature_used", "report_created", "export_completed")
                        else None
                    )
                    event(
                        user,
                        product,
                        session,
                        timestamp + timedelta(minutes=step + 1),
                        kind,
                        device,
                        feature,
                    )
            if dropout < days:
                event(
                    user,
                    product,
                    f"u{user}-exit",
                    origin + timedelta(days=dropout, hours=12),
                    "churn_signal",
                    device,
                )
            if plan != "free":
                started = signup + timedelta(days=int(rng.integers(1, 22)))
                cancelled = None
                if dropout < days and rng.random() < 0.8:
                    cancelled = origin + timedelta(days=dropout, hours=13)
                elif rng.random() < 0.07:
                    cancelled = started + timedelta(
                        days=int(rng.integers(35, max(36, days - signup_day - 22)))
                    )
                    if cancelled >= end:
                        cancelled = None
                price = {"starter": 19, "pro": 49, "enterprise": 149}[plan]
                subscription = counts["subscriptions"] + 1
                add(
                    "subscriptions",
                    [
                        subscription,
                        user,
                        product,
                        plan,
                        started,
                        cancelled,
                        price,
                        "cancelled" if cancelled else "active",
                    ],
                )
                event(
                    user,
                    product,
                    f"u{user}-purchase",
                    started - timedelta(minutes=5),
                    "upgrade_started",
                    device,
                )
                event(user, product, f"u{user}-purchase", started, "purchase_completed", device)
                billed = started
                while billed < (cancelled or end):
                    status = "failed" if rng.random() < 0.025 else "succeeded"
                    add(
                        "transactions",
                        [
                            counts["transactions"] + 1,
                            subscription,
                            user,
                            product,
                            billed,
                            price,
                            "USD",
                            status,
                        ],
                    )
                    billed += timedelta(days=30)
            for _ in range(int(rng.poisson(0.6 + 0.8 * (1 - engagement)))):
                opened = signup + timedelta(
                    days=int(rng.integers(1, max(2, activity_end - signup_day))), hours=1
                )
                if opened >= end:
                    continue
                resolved = opened + timedelta(hours=int(rng.integers(1, 97)))
                add(
                    "support_tickets",
                    [
                        counts["support_tickets"] + 1,
                        user,
                        product,
                        opened,
                        resolved if resolved < end else None,
                        str(rng.choice(["low", "medium", "high"], p=[0.4, 0.45, 0.15])),
                        str(rng.choice(["billing", "bug", "how_to"])),
                    ],
                )
                event(
                    user,
                    product,
                    f"u{user}-support-{counts['support_tickets']}",
                    opened,
                    "support_opened",
                    device,
                )
    finally:
        for handle in files.values():
            handle.close()
    manifest = {
        "seed": settings.seed,
        "users": settings.users,
        "start": str(settings.start),
        "end": str(settings.end),
        "counts": counts,
        "sha256": {
            t: hashlib.sha256((folder / f"{t}.csv").read_bytes()).hexdigest() for t in TABLE_COLUMNS
        },
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
