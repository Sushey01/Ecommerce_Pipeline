"""
Model Training Module
Loads processed data, loads tuned hyperparameters, trains model, logs to MLflow
"""

import os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import mlflow
import mlflow.sklearn

# Monkeypatch requests to bypass MLflow Host Header check
import requests
original_request = requests.Session.request
def custom_request(self, method, url, *args, **kwargs):
    if "mlflow" in url:
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["Host"] = "localhost:5001"
        kwargs["headers"] = headers
    return original_request(self, method, url, *args, **kwargs)
requests.Session.request = custom_request

from mlflow.store.artifact.local_artifact_repo import LocalArtifactRepository
original_local_init = LocalArtifactRepository.__init__
def custom_local_init(self, artifact_uri, *args, **kwargs):
    base_dir = "/opt/airflow" if os.path.exists("/opt/airflow") else str(MODELS_DIR.parent)
    if artifact_uri.startswith("file:///mlflow/mlruns"):
        artifact_uri = artifact_uri.replace("file:///mlflow/mlruns", f"file://{base_dir}/mlruns")
    elif artifact_uri.startswith("/mlflow/mlruns"):
        artifact_uri = artifact_uri.replace("/mlflow/mlruns", f"{base_dir}/mlruns")
    original_local_init(self, artifact_uri, *args, **kwargs)
LocalArtifactRepository.__init__ = custom_local_init

from src.database import read_from_db
from src.redis_client import get_redis_client, get_dataframe

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

def train():
    """Train the best model found during tuning and save model artifacts"""
    print("🤖 Task 4: Training Model...")
    
    # Load data from Redis (or fallback to DB)
    r = get_redis_client()
    train_X = None
    train_y = None
    
    if r:
        print("📥 Attempting to load train split from Redis...")
        train_X = get_dataframe(r, 'dataset:train_X')
        train_y = get_dataframe(r, 'dataset:train_y')
        
    if train_X is None or train_y is None:
        print("⚠️ Train split not found in Redis. Falling back to loading from DB...")
        df = read_from_db("SELECT * FROM processed_ecommerce_data")
        target_col = 'ad_clicked'
        meta_cols = ['pipeline_run_id', 'ingestion_ts']
        X = df.drop(columns=[target_col] + [c for c in meta_cols if c in df.columns])
        y = df[target_col]
        
        # Split using the same random state
        from sklearn.model_selection import train_test_split
        train_X, _, train_y, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
    # Ensure y is a 1D Series
    if isinstance(train_y, pd.DataFrame):
        train_y = train_y.iloc[:, 0]
        
    # Load best model configuration
    config_file = MODELS_DIR / 'best_model_config.pkl'
    if config_file.exists():
        print(f"📂 Loading best model config from {config_file}")
        winner_config = joblib.load(config_file)
        model_type = winner_config['model_type']
        best_params = winner_config['best_params']
    else:
        print("⚠️ Best model config not found. Defaulting to Random Forest.")
        model_type = 'RandomForest'
        best_params = {'n_estimators': 100, 'max_depth': 10}
        
    # Instantiate model
    print(f"Instantiating model type: {model_type} with parameters {best_params}")
    if model_type == 'LogisticRegression':
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(**best_params, max_iter=1000, random_state=42)
    elif model_type == 'XGBoost':
        try:
            from xgboost import XGBClassifier
            model = XGBClassifier(**best_params, random_state=42, eval_metric='logloss', n_jobs=-1)
        except ImportError:
            print("⚠️ XGBoost is not available. Falling back to Random Forest.")
            model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    else:
        # RandomForest is default
        model = RandomForestClassifier(**best_params, random_state=42, n_jobs=-1)
        
    print(f"⏱️ Training {model_type} classifier on the training split (80%)...")
    model.fit(train_X, train_y)
    
    # Save model locally as best_model.pkl
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_file = MODELS_DIR / 'best_model.pkl'
    joblib.dump(model, model_file)
    print(f"💾 Saved best model to: {model_file}")
    
    # Save feature names
    features_file = MODELS_DIR / 'feature_names.pkl'
    feature_names = train_X.columns.tolist()
    joblib.dump(feature_names, features_file)
    print(f"💾 Saved feature names to: {features_file}")
    
    # Log to MLflow
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("E-Commerce Ad Click Prediction")
    
    with mlflow.start_run():
        mlflow.log_param("selected_model_type", model_type)
        mlflow.log_params(best_params)
        mlflow.sklearn.log_model(model, "best_model")
        mlflow.log_artifact(str(features_file))
        print(f"✅ Logged parameters and model to MLflow at {mlflow_tracking_uri}")

    print("✅ Training complete!")

if __name__ == '__main__':
    train()

