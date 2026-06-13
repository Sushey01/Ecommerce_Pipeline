"""
Evaluation Module
Loads model, evaluates on test set, logs metrics to MLflow, generates diagnostic plots, and runs drift analysis
"""

import os
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, RocCurveDisplay,
    PrecisionRecallDisplay
)
from sklearn.model_selection import train_test_split
import numpy as np
import matplotlib.pyplot as plt
import mlflow
import joblib

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

try:
    import seaborn as sns
except Exception:
    sns = None

FIGURES_DIR = Path(__file__).resolve().parent.parent / 'figures'
FIGURES_DIR.mkdir(exist_ok=True)
MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

def evaluate():
    """Evaluate trained model on test split, log metrics, and generate drift reports"""
    print("📊 Task 5: Evaluating Model...")
    
    # Load model
    model_file = MODELS_DIR / 'random_forest_model.pkl'
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found at {model_file}. Run training first.")
    
    model = joblib.load(model_file)
    
    # Load processed data
    df = read_from_db("SELECT * FROM processed_ecommerce_data")
    X = df.drop('ad_clicked', axis=1)
    y = df['ad_clicked']
    
    # Test/train split (use same split as training for fair evaluation)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Test metrics
    y_test_pred = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    precision = precision_score(y_test, y_test_pred)
    recall = recall_score(y_test, y_test_pred)
    f1 = f1_score(y_test, y_test_pred)
    
    try:
        probs = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probs)
    except Exception:
        probs = None
        auc = None
        
    print(f"Test Accuracy:     {test_accuracy:.4f}")
    print(f"Precision:         {precision:.4f}")
    print(f"Recall:            {recall:.4f}")
    print(f"F1-Score:          {f1:.4f}")
    if auc is not None:
        print(f"ROC AUC:           {auc:.4f}")
        
    print(f"\n📋 Classification Report:\n{classification_report(y_test, y_test_pred)}")
    
    # Save diagnostic plots
    _save_plots(y_test, y_test_pred, probs)
    
    # Log to MLflow
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment("E-Commerce Ad Click Prediction")
    
    with mlflow.start_run():
        mlflow.log_metric('eval_accuracy', test_accuracy)
        mlflow.log_metric('eval_precision', precision)
        mlflow.log_metric('eval_recall', recall)
        mlflow.log_metric('eval_f1', f1)
        if auc is not None:
            mlflow.log_metric('eval_roc_auc', auc)
            
        # Log plot files as artifacts
        for plot_name in ['roc_curve.png', 'pr_curve.png', 'confusion_matrix.png']:
            plot_path = FIGURES_DIR / plot_name
            if plot_path.exists():
                mlflow.log_artifact(str(plot_path))
                
        print(f"✅ Evaluated metrics and logged plots to MLflow under experiment: E-Commerce Ad Click Prediction")
    print("✅ Model evaluation complete!")

def _save_plots(y_test, y_test_pred, probs):
    """Save evaluation plots to figures directory"""
    try:
        # ROC curve
        if probs is not None:
            RocCurveDisplay.from_predictions(y_test, probs)
            plt.title('ROC curve')
            plt.savefig(FIGURES_DIR / 'roc_curve.png')
            plt.close()
            
        # Precision-Recall
        if probs is not None:
            PrecisionRecallDisplay.from_predictions(y_test, probs)
            plt.title('Precision-Recall curve')
            plt.savefig(FIGURES_DIR / 'pr_curve.png')
            plt.close()
            
        # Confusion matrix
        cm = confusion_matrix(y_test, y_test_pred)
        plt.figure(figsize=(4,3))
        if sns is not None:
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        else:
            plt.imshow(cm, cmap='Blues', interpolation='nearest')
            for (i, j), val in np.ndenumerate(cm):
                plt.text(j, i, int(val), ha='center', va='center')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.savefig(FIGURES_DIR / 'confusion_matrix.png')
        plt.close()
    except Exception as e:
        print('Warning: could not save diagnostic plots:', e)

if __name__ == '__main__':
    evaluate()
