import sys
import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def run_monitoring_task():
    from src.monitoring import run_system_monitoring
    run_system_monitoring()

default_args = {
    "owner": "shekhar",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

with DAG(
    dag_id="mlops_monitoring",
    default_args=default_args,
    description="Continuous parallel monitoring of MLOps stack, cache, DB, and drift detection",
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",  # Run every 5 minutes
    catchup=False,
    max_active_runs=1,
) as dag:

    task_monitor = PythonOperator(
        task_id="run_monitoring",
        python_callable=run_monitoring_task,
        do_xcom_push=False,
    )

    task_monitor
