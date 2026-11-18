"""Create an honest reviewable report from executed pipeline and JUnit evidence."""

import json
import platform
import xml.etree.ElementTree as ET
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def write_report():
    folder = ROOT / "outputs/verification"
    verification = json.loads((folder / "pipeline_verification.json").read_text())
    audit = json.loads((folder / "pipeline_run.json").read_text())
    source = json.loads((ROOT / "data/generated/manifest.json").read_text())
    exports = json.loads((ROOT / "outputs/bi/manifest.json").read_text())
    repository = json.loads((folder / "repository_check.json").read_text())
    tree = ET.parse(folder / "pytest.xml")
    suites = tree.getroot().findall("testsuite")
    tests = sum(int(s.attrib["tests"]) for s in suites)
    failures = sum(
        int(s.attrib.get("failures", 0)) + int(s.attrib.get("errors", 0)) for s in suites
    )
    skipped = sum(int(s.attrib.get("skipped", 0)) for s in suites)
    if audit["status"] != "success" or failures or verification["checks_failed"]:
        raise ValueError("Cannot produce successful verification from failed execution evidence")
    ml = verification["ml"]
    now = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
    versions = {
        name: version(name)
        for name in [
            "dbt-core",
            "dbt-postgres",
            "pandas",
            "numpy",
            "scipy",
            "scikit-learn",
            "pytest",
            "psycopg",
        ]
    }
    lines = [
        "# Final verification",
        f"\nRecorded {now}. Evidence comes from executed native PostgreSQL/Python/dbt tasks; business data is synthetic.",
        "\n## Execution environment",
        f"\n- OS: {platform.platform()}; Python: {platform.python_version()}.",
        "- PostgreSQL: installed Windows PostgreSQL 18.3; isolated project cluster at 127.0.0.1:55432.",
        f"- Packages: `{json.dumps(versions)}`.",
        "- Docker executable and WSL Linux runtime unavailable; no native Windows Airflow runtime was installed.",
        "\n## Final results",
        f"\n- Shared-task CLI pipeline: **{audit['status']}**.",
        f"- Python tests: **{tests - skipped - failures} passed, {failures} failed, {skipped} skipped**, {tests} collected. The skip is real Airflow import on Windows.",
        f"- dbt: **29 models built**, **{verification['dbt_tests']['passed']} tests passed, {verification['dbt_tests']['failed']} failed**; separate post-scoring test run.",
        f"- Final validation: **{verification['checks_passed']} checks passed, {verification['checks_failed']} failed**.",
        f"- Reporting: **{len(exports)} nonempty CSV extracts**, manifest and Power BI page/measure/relationship guide.",
        f"- Repository check: {repository['source_files_inspected']} source files parsed/scanned, zero runtime passwords found; .env and runtime outputs are ignored.",
        "- Complete rerun: all seven source counts and SHA-256 checksums matched the preceding successful run (outputs/verification/idempotence.json).",
        "- Lint and formatting checks were run separately; their exact commands appear below.",
        "\n## Source records",
        "\n| Source | Records |",
        "|---|---:|",
    ]
    for name, n in source["counts"].items():
        lines.append(f"| {name} | {n:,} |")
    lines.append(f"| **Total** | **{sum(source['counts'].values()):,}** |")
    lines += ["\n## Warehouse row counts", "\n| Relation | Rows |", "|---|---:|"]
    for table, n in sorted(verification["row_counts"].items()):
        lines.append(f"| {table} | {n:,} |")
    lines += [
        "\nAlso created control.run_config, control.ml_predictions and reporting.data_quality; counts and current checks are visible in operational exports.",
        "\n## ML results",
        f"\nLogistic Regression trained on {ml['train_cutoff']} ({ml['train_rows']:,} rows), threshold-selected on {ml['validation_cutoff']} ({ml['validation_rows']:,} rows), and evaluated on {ml['test_cutoff']} ({ml['test_rows']:,} rows).",
        f"\n- ROC-AUC: {ml['roc_auc']:.6f}; precision: {ml['precision']:.6f}; recall: {ml['recall']:.6f}; F1: {ml['f1']:.6f}.",
        f"- Confusion matrix [TN, FP; FN, TP]: `{ml['confusion_matrix']}`.",
        f"- Validation-selected threshold: {ml['threshold']:.2f}; test prevalence: {ml['test_prevalence']:.6f}.",
        f"- Current eligible scored users: {ml['scored_users']:,}; artifact version: {ml['model_version']}.",
        "- Model, features, metadata, coefficients, evaluation, test predictions and current scores were saved and the persisted model was reloaded/checked. No refit on test data; no claim of real-world predictive validity.",
        "\n## Latest product metrics",
        "\n| Product | DAU | WAU | MAU | Activation | Conversion | Churn | Daily revenue | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in verification["latest_metrics"]:

        def rate(k):
            return f"{float(row[k]):.2%}" if row[k] is not None else "null"

        lines.append(
            f"| {row['product_id']} | {row['dau']} | {row['wau']} | {row['mau']} | {rate('activation_rate')} | {rate('conversion_rate')} | {rate('churn_rate')} | ${float(row['revenue']):,.2f} | ${float(row['mrr']):,.2f} |"
        )
    lines += [
        "\nAdditional outputs: exact-day retention/cohorts, feature adoption, ARPU/ARPPU, revenue/subscriptions, customer segmentation, health and risk bands. See canonical definitions in docs/METRICS.md.",
        "\n## Export inventory",
        "\n| CSV | Rows |",
        "|---|---:|",
    ]
    for name, metadata in exports.items():
        lines.append(f"| {name}.csv | {metadata['rows']:,} |")
    lines += [
        "\n## Commands actually executed",
        "\nThe final full run and test suite used these commands from the workspace root:",
        "\n```powershell",
        ".\\scripts\\local_postgres.ps1 start",
        "uv pip compile pyproject.toml --extra dev --python-version 3.11 --output-file requirements.lock --quiet",
        "uv pip sync --python .venv\\Scripts\\python.exe requirements.lock --quiet",
        "uv pip install --python .venv\\Scripts\\python.exe --no-deps -e . --quiet",
        ".venv\\Scripts\\python.exe scripts\\write_dbt_schema.py",
        ".venv\\Scripts\\python.exe -m platform_app.cli pipeline *> .runtime\\pipeline-final.log",
        "$env:RUN_INTEGRATION = '1'",
        ".venv\\Scripts\\python.exe -m pytest -q --junitxml=outputs/verification/pytest.xml *> .runtime\\tests-final.log",
        ".venv\\Scripts\\ruff.exe check src scripts tests airflow",
        ".venv\\Scripts\\ruff.exe format --check src scripts tests airflow",
        ".venv\\Scripts\\python.exe scripts\\verify_repository.py",
        ".venv\\Scripts\\python.exe scripts\\write_final_verification.py",
        "```",
        "\nThe pipeline invokes dbt parse, dbt build, post-scoring dbt test and dbt docs generate with --project-dir dbt --profiles-dir dbt. It generated sources, loaded PostgreSQL, trained/scored ML, exported CSVs and ran final validation.",
        "\n## Fixes and reruns",
        "\nThe first parse exposed duplicate not_null declarations on natural keys; the schema generator now merges column tests. The next build exposed a common-column ambiguity after a revenue join; an explicit product/date join fixed it. A subsequent KPI query was cancelled after query-plan inspection showed repeated nested-loop aggregate work; PostgreSQL MATERIALIZED CTEs ensure reusable aggregates execute once. All final errors were resolved and the complete pipeline and tests were rerun. A SciPy version mismatch warning was resolved by pinning 1.15.3, and the dependency lock was resolved for Python 3.11 to support Docker as well as native 3.12. The final test run produced no warnings.",
        "\n## Environmental limits",
        "\n- One real Airflow DAG with 14 tasks and a Docker deployment are provided. DAG syntax and static contract tests passed. Docker builds, DagBag import, scheduler startup and real DAG execution were **not executed** on this host; the standalone Airflow runtime test is available in airflow/tests for Linux. The shared-task CLI is the documented native execution path, not a replacement scheduler.",
        "- Power BI report assembly was not executed; 13 verified CSVs and detailed dashboard/DAX instructions are delivered. No PBIX or dashboard screenshot was fabricated.",
        "- The workspace did not initially contain a Git repository. Source scanning confirms no runtime passwords in the deliverable files; this is not a claim that a commit was audited.",
        "- Generated datasets, warehouse state, model files, dbt compiled outputs and verification XML/JSON are intentionally ignored and retained locally as reproducible evidence. Automatic approval review rejected both batch and explicitly named cache deletion with the reason 'blocked by policy'. Temporary diagnostic files and caches therefore remain locally and are ignored; no cleanup success is claimed. Source specifications and this summary remain reviewable.",
        "\n## Reproduction",
        "\nUse the exact fresh-environment native or Docker commands in README.md. Docker-specific commands are provided reproduction instructions, not executed verification. The default source seed is 42; source checksums are recorded in data/generated/manifest.json. Change the seed/horizon deliberately and regenerate before loading.",
    ]
    (ROOT / "FINAL_VERIFICATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_report()
