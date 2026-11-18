"""Run with Airflow's Python inside the scheduler image, not analytics-venv."""

from pathlib import Path

from airflow.models import DagBag


def test_real_dag_import_and_chain():
    bag = DagBag(
        dag_folder=str(Path(__file__).resolve().parents[1] / "dags"), include_examples=False
    )
    assert not bag.import_errors
    dag = bag.get_dag("product_analytics_pipeline")
    assert dag is not None and len(dag.tasks) == 14
    assert dag.max_active_runs == 1
    assert dag.get_task("train_churn_model").downstream_task_ids == {"dbt_final_tests"}
    assert dag.get_task("load_raw").retries == 2
    assert dag.get_task("generate_data").upstream_task_ids == set()
    assert dag.get_task("dbt_documentation").downstream_task_ids == set()
