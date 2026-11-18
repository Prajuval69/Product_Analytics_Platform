"""Shared tasks for the CLI and real Airflow BashOperators, with checked subprocesses."""

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone

from platform_app.config import Settings
from platform_app.database import load_raw
from platform_app.generate import generate
from platform_app.ml import feature_dataset, train
from platform_app.quality import raw_checks, record_checks, verify
from platform_app.reporting import export

LOG = logging.getLogger(__name__)


def dbt(settings: Settings, command: str, selection=None):
    executable = shutil.which("dbt") or str(settings.root / ".venv" / "Scripts" / "dbt.exe")
    args = [
        executable,
        *command.split(),
        "--project-dir",
        str(settings.root / "dbt"),
        "--profiles-dir",
        str(settings.root / "dbt"),
    ]
    if selection:
        args += ["--select", selection]
    environment = dict(os.environ)
    environment["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    subprocess.run(args, cwd=settings.root, env=environment, check=True)
    if command in ("build", "test"):
        results = json.loads((settings.root / "dbt/target/run_results.json").read_text())
        tests = [r for r in results["results"] if r["unique_id"].startswith("test.")]
        summary = {
            "passed": sum(r["status"] == "pass" for r in tests),
            "failed": sum(r["status"] != "pass" for r in tests),
            "command": " ".join(args),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        folder = settings.outputs / "verification"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "dbt_test_summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        record_checks(
            [
                (
                    "dbt_test_suite",
                    summary["passed"] > 0 and summary["failed"] == 0,
                    summary["passed"],
                )
            ]
        )


def execute_task(settings: Settings, name: str):
    tasks = {
        "generate": lambda: generate(settings),
        "load": lambda: load_raw(settings),
        "quality": lambda: raw_checks(settings),
        "dbt-parse": lambda: dbt(settings, "parse"),
        "dbt-build": lambda: dbt(settings, "build"),
        "dbt-staging": lambda: dbt(settings, "run", "staging"),
        "dbt-intermediate": lambda: dbt(settings, "run", "intermediate"),
        "dbt-marts": lambda: dbt(settings, "run", "marts"),
        "dbt-test": lambda: dbt(settings, "test"),
        "dbt-docs": lambda: dbt(settings, "docs generate"),
        "features": lambda: feature_dataset(settings),
        "ml": lambda: train(settings),
        "export": lambda: export(settings),
        "verify": lambda: verify(settings),
    }
    if name not in tasks:
        raise ValueError(f"Unknown task {name}")
    started = time.monotonic()
    LOG.info(json.dumps({"task": name, "status": "started"}))
    try:
        result = tasks[name]()
    except Exception:
        LOG.exception(json.dumps({"task": name, "status": "failed"}))
        raise
    LOG.info(
        json.dumps(
            {"task": name, "status": "success", "seconds": round(time.monotonic() - started, 2)}
        )
    )
    return result


def run(settings: Settings):
    folder = settings.outputs / "verification"
    folder.mkdir(parents=True, exist_ok=True)
    audit = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "executor": "synchronous CLI (shared Airflow tasks)",
        "tasks": [],
        "status": "running",
    }
    path = folder / "pipeline_run.json"
    try:
        for task in [
            "generate",
            "load",
            "quality",
            "dbt-parse",
            "dbt-build",
            "features",
            "ml",
            "dbt-test",
            "export",
            "verify",
            "dbt-docs",
        ]:
            start = time.monotonic()
            execute_task(settings, task)
            audit["tasks"].append(
                {"task": task, "status": "success", "seconds": round(time.monotonic() - start, 2)}
            )
            path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
        audit["status"] = "success"
    except Exception:
        audit["status"] = "failed"
        audit["failed_task"] = task
        raise
    finally:
        audit["finished_at"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
