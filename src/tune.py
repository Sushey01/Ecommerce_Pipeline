"""
Hyperparameter Tuning Module
Loads processed data, runs RandomizedSearchCV over multiple models, and saves the best model config
"""

import os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import mlflow

# Import XGBoost dynamically
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

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

def tune():
    """Run RandomizedSearchCV to find best hyperparameters for multiple classifiers and save config"""
    print("🤖 Tuning Stage: Comparing models and tuning hyperparameters...")
    
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
        
    print(f"📊 Training feature set shape: {train_X.shape}")
    
    # Define models and their parameter distributions
    models_config = {
        'LogisticRegression': {
            'model': LogisticRegression(max_iter=1000, random_state=42),
            'params': {
                'C': [0.01, 0.1, 1.0, 10.0],
                'solver': ['liblinear', 'lbfgs']
            }
        },
        'RandomForest': {
            'model': RandomForestClassifier(random_state=42, n_jobs=-1),
            'params': {
                'n_estimators': [50, 100],
                'max_depth': [3, 5, 8],
                'min_samples_split': [2, 5]
            }
        }
    }
    
    if XGB_AVAILABLE:
        print("XGBoost is available. Adding to comparison search.")
        models_config['XGBoost'] = {
            'model': XGBClassifier(random_state=42, eval_metric='logloss', n_jobs=-1),
            'params': {
                'n_estimators': [50, 100],
                'max_depth': [3, 5],
                'learning_rate': [0.01, 0.1]
            }
        }
    else:
        print("⚠️ XGBoost is not available. Skipping XGBoost tuning.")
        
    # Setup MLflow
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("E-Commerce Ad Click Prediction")
    
    best_score = -1.0
    best_model_name = None
    best_params = None
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for name, config in models_config.items():
        print(f"⏱️ Tuning {name}...")
        
        n_iter = min(4, len(config['params'])) if name == 'LogisticRegression' else 4
        
        search = RandomizedSearchCV(
            config['model'],
            config['params'],
            n_iter=n_iter,
            cv=cv,
            scoring='roc_auc',
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        
        search.fit(train_X, train_y)
        score = search.best_score_
        print(f"   Best ROC-AUC: {score:.4f} with {search.best_params_}")
        
        # Log tuning runs to MLflow
        with mlflow.start_run(run_name=f"Tune_{name}"):
            mlflow.log_param("model_type", name)
            mlflow.log_params(search.best_params_)
            mlflow.log_metric("mean_val_roc_auc", score)
            
        if score > best_score:
            best_score = score
            best_model_name = name
            best_params = search.best_params_
            
    print(f"🥇 Winner: {best_model_name} with ROC-AUC {best_score:.4f}")
    
    # Save the winner configuration
    winner_config = {
        'model_type': best_model_name,
        'best_params': best_params,
        'val_roc_auc': best_score
    }
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    config_file = MODELS_DIR / 'best_model_config.pkl'
    joblib.dump(winner_config, config_file)
    print(f"💾 Saved best model config to: {config_file}")

if __name__ == '__main__':
    tune()

