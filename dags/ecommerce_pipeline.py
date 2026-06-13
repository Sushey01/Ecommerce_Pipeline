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
from datetime import datetime

# Wrapper callables to defer heavy library imports
def run_ingest_task():
    from src.extract import extract
    from src.load import load
    print("📥 Starting data extraction...")
    extract()
    print("📤 Starting data loading...")
    load()

def run_preprocess_task():
    from src.transform import transform
    return transform()

def run_tuning_task():
    from src.tune import tune
    return tune()

def run_train_task():
    from src.train import train
    return train()

def run_evaluate_task():
    from src.evaluate import evaluate
    return evaluate()

default_args = {
    "owner": "shekhar",
}

with DAG(
    dag_id="ecommerce_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:

    task_ingest = PythonOperator(
        task_id="ingest_data",
        python_callable=run_ingest_task,
        do_xcom_push=False,
    )

    task_preprocess = PythonOperator(
        task_id="preprocess_data",
        python_callable=run_preprocess_task,
        do_xcom_push=False,
    )

    task_tuning = PythonOperator(
        task_id="tune_hyperparameters",
        python_callable=run_tuning_task,
        do_xcom_push=False,
    )

    task_train = PythonOperator(
        task_id="train_model",
        python_callable=run_train_task,
        do_xcom_push=False,
    )

    task_evaluate = PythonOperator(
        task_id="evaluate_model",
        python_callable=run_evaluate_task,
        do_xcom_push=False,
    )

    (
        task_ingest
        >> task_preprocess
        >> task_tuning
        >> task_train
        >> task_evaluate
    )

