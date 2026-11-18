import pandas as pd
import pytest

from platform_app.config import ROOT
from platform_app.database import load_raw
from platform_app.quality import validate_frame


@pytest.mark.parametrize(
    "case", ["duplicate", "null_key", "null_required", "invalid_category", "orphan", "empty"]
)
def test_invalid_fixture_rejected(case):
    frame = pd.DataFrame(
        {
            "id": [1, 2],
            "parent": [1, 1],
            "plan": ["free", "pro"],
            "timestamp": ["2025-01-01", "2025-01-02"],
        }
    )
    if case == "duplicate":
        frame.loc[1, "id"] = 1
    elif case == "null_key":
        frame.loc[1, "id"] = None
    elif case == "null_required":
        frame.loc[1, "timestamp"] = None
    elif case == "invalid_category":
        frame.loc[1, "plan"] = "unknown"
    elif case == "orphan":
        frame.loc[1, "parent"] = 999
    elif case == "empty":
        frame = frame.iloc[0:0]
    with pytest.raises(ValueError):
        validate_frame(frame, "id", ["timestamp"], {"plan": ["free", "pro"]}, {"parent": [1]})


def test_valid_frame_accepted():
    frame = pd.DataFrame(
        {
            "id": [1, 2],
            "parent": [1, 1],
            "plan": ["free", "pro"],
            "timestamp": ["2025-01-01", "2025-01-02"],
        }
    )
    validate_frame(frame, "id", ["timestamp"], {"plan": ["free", "pro"]}, {"parent": [1]})


def test_committed_bad_fixture_is_quarantined():
    frame = pd.read_csv(ROOT / "data/fixtures/invalid_users.csv")
    with pytest.raises(ValueError):
        validate_frame(
            frame,
            "user_id",
            ["signup_at"],
            {"plan": ["free", "pro"]},
            {"product_id": [1, 2, 3, 4, 5]},
        )


def test_checksum_failure_before_database_write(sample, tmp_path):
    from dataclasses import replace

    from platform_app.generate import generate

    config = replace(sample[0], root=tmp_path)
    generate(config)
    with (config.generated / "events.csv").open("a") as file:
        file.write("tampered")
    with pytest.raises(ValueError, match="checksum"):
        load_raw(config)


def test_configuration_mismatch_before_database_write(sample):
    from dataclasses import replace

    with pytest.raises(ValueError, match="configuration"):
        load_raw(replace(sample[0], seed=999))
