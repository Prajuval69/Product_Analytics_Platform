import ast
from unittest.mock import patch

import pytest
import yaml

from platform_app.config import ROOT, Settings
from platform_app.pipeline import execute_task


def test_unknown_task_rejected():
    with pytest.raises(ValueError, match="Unknown task"):
        execute_task(Settings(), "not-a-task")


def test_failure_propagates():
    with patch("platform_app.pipeline.generate", side_effect=RuntimeError("intentional failure")):
        with pytest.raises(RuntimeError, match="intentional"):
            execute_task(Settings(), "generate")


def test_dag_syntax_and_stage_contract():
    tree = ast.parse((ROOT / "airflow/dags/product_analytics_pipeline.py").read_text())
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)]
    stages = next(
        ast.literal_eval(n.value)
        for n in assignments
        if any(isinstance(t, ast.Name) and t.id == "STAGES" for t in n.targets)
    )
    assert len(stages) == 14 and len({task for task, _ in stages}) == 14
    assert stages[0] == ("generate_data", "generate")
    assert stages[-2] == ("final_validation", "verify")
    commands = {command for _, command in stages}
    assert {"dbt-staging", "dbt-intermediate", "dbt-marts", "dbt-test", "ml", "export"} <= commands


def test_compose_structure_and_secret_references():
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    services = compose["services"]
    assert services["warehouse"]["ports"] == ["127.0.0.1:55432:5432"]
    assert "PG_PASSWORD:?" in services["warehouse"]["environment"]["POSTGRES_PASSWORD"]
    assert (
        services["airflow-scheduler"]["environment"]["AIRFLOW__CORE__EXECUTOR"] == "LocalExecutor"
    )
    assert (
        services["airflow-webserver"]["depends_on"]["airflow-init"]["condition"]
        == "service_completed_successfully"
    )


def test_every_sql_model_documented():
    documented = {
        m["name"] for m in yaml.safe_load((ROOT / "dbt/models/schema.yml").read_text())["models"]
    }
    sql_models = {p.stem for p in (ROOT / "dbt/models").rglob("*.sql")}
    assert documented == sql_models
    assert len(sql_models) == 29


@pytest.mark.airflow
def test_real_airflow_dag_load_and_dependencies():
    if __import__("sys").platform == "win32":
        pytest.skip("Apache Airflow requires Linux/WSL/Docker; no fake Airflow module used")
    pytest.importorskip("airflow.models")
    from airflow.models import DagBag

    bag = DagBag(dag_folder=str(ROOT / "airflow/dags"), include_examples=False)
    assert not bag.import_errors
    dag = bag.get_dag("product_analytics_pipeline")
    assert dag is not None and len(dag.tasks) == 14 and dag.max_active_runs == 1
    assert dag.get_task("train_churn_model").downstream_task_ids == {"dbt_final_tests"}
    assert dag.get_task("load_raw").retries == 2
