"""
Airflow DAG: MLOps ecommerce pipeline
Orchestrates: Data Ingestion → Preprocessing → Model Training
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Import pipeline functions
from data_ingestion import download_dataset
from preprocessing import run_etl_pipeline
from train_model import run_training_pipeline

default_args = {
    'owner': 'mlops',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

dag = DAG(
    'ecommerce_ml_pipeline',
    default_args=default_args,
    description='MLOps Pipeline: Fetch → ETL → Train',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
)

# Task 1: Data Ingestion
def task_data_ingestion():
    print("🔗 Task 1: Downloading dataset...")
    download_dataset()
    print("✅ Dataset ready")

task_ingest = PythonOperator(
    task_id='data_ingestion',
    python_callable=task_data_ingestion,
    dag=dag,
)

# Task 2: Preprocessing
def task_preprocessing():
    print("🧹 Task 2: Running ETL pipeline...")
    run_etl_pipeline()
    print("✅ Data preprocessed")

task_preprocess = PythonOperator(
    task_id='preprocessing',
    python_callable=task_preprocessing,
    dag=dag,
)

# Task 3: Model Training
def task_training():
    print("🤖 Task 3: Training model...")
    run_training_pipeline()
    print("✅ Model trained")

task_train = PythonOperator(
    task_id='model_training',
    python_callable=task_training,
    dag=dag,
)

# Define dependencies
task_ingest >> task_preprocess >> task_train
