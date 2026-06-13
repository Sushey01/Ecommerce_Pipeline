"""
Model Training Module
Loads processed data, loads tuned hyperparameters, trains model, logs to MLflow
"""

import os
from pathlib import Path
import joblib
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

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

def train():
    """Train Random Forest model using best parameters and save model artifacts"""
    print("🤖 Task 4: Training Model...")
    
    # Load processed data
    df = read_from_db("SELECT * FROM processed_ecommerce_data")
    
    # Separate features and target
    X = df.drop('ad_clicked', axis=1)
    y = df['ad_clicked']
    
    # Load best params if available
    params_file = MODELS_DIR / 'best_params.pkl'
    if params_file.exists():
        print(f"📂 Loading best parameters from {params_file}")
        best_params = joblib.load(params_file)
    else:
        print("⚠️ Best parameters file not found. Using default parameters.")
        best_params = {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42
        }
        
    # Ensure random_state is set for reproducibility
    best_params['random_state'] = 42
    
    # Initialize and train model
    model = RandomForestClassifier(**best_params, n_jobs=-1)
    print("⏱️ Training Random Forest classifier...")
    model.fit(X, y)
    
    # Save model locally
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_file = MODELS_DIR / 'random_forest_model.pkl'
    joblib.dump(model, model_file)
    print(f"💾 Saved model to: {model_file}")
    
    # Save feature names
    features_file = MODELS_DIR / 'feature_names.pkl'
    feature_names = X.columns.tolist()
    joblib.dump(feature_names, features_file)
    print(f"💾 Saved feature names to: {features_file}")
    
    # Log to MLflow
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("E-Commerce Ad Click Prediction")
    
    with mlflow.start_run():
        mlflow.log_params(best_params)
        mlflow.sklearn.log_model(model, "random_forest_model")
        mlflow.log_artifact(str(features_file))
        print(f"✅ Logged parameters and model to MLflow at {mlflow_tracking_uri}")

    print("✅ Training complete!")

if __name__ == '__main__':
    train()
