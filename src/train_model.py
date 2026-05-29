"""
Random Forest Model Training
Trains Random Forest classifier on preprocessed ecommerce data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import joblib
import json
from datetime import datetime

MODELS_DIR = Path(__file__).parent.parent / 'models'

def load_processed_data():
    """Load preprocessed data"""
    data_file = MODELS_DIR / 'processed_data.csv'
    df = pd.read_csv(data_file)
    print(f"📊 Loaded: {data_file.name}")
    print(f"   Shape: {df.shape}")
    return df

def prepare_features_target(df):
    """Separate features and target"""
    X = df.drop('ad_clicked', axis=1)
    y = df['ad_clicked']
    
    print(f"\n📋 Feature set: {X.shape}")
    print(f"   Features: {list(X.columns)}")
    print(f"   Target: {y.value_counts().to_dict()}")
    
    return X, y

def train_random_forest(X, y):
    """Train Random Forest classifier"""
    print("\n🚀 Training Random Forest...\n")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"✅ Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    print("✅ Model trained")
    
    return model, X_train, X_test, y_train, y_test

def evaluate_model(model, X_train, X_test, y_train, y_test):
    """Evaluate model performance"""
    print("\n📊 Model Evaluation:\n")
    
    # Training metrics
    y_train_pred = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, y_train_pred)
    
    # Test metrics
    y_test_pred = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    precision = precision_score(y_test, y_test_pred)
    recall = recall_score(y_test, y_test_pred)
    f1 = f1_score(y_test, y_test_pred)
    
    print(f"Training Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy:     {test_accuracy:.4f}")
    print(f"Precision:         {precision:.4f}")
    print(f"Recall:            {recall:.4f}")
    print(f"F1-Score:          {f1:.4f}")
    
    print(f"\n📋 Classification Report:\n{classification_report(y_test, y_test_pred)}")
    
    metrics = {
        'train_accuracy': train_accuracy,
        'test_accuracy': test_accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
    return metrics

def save_model(model, X_train):
    """Save trained model"""
    model_file = MODELS_DIR / 'random_forest_model.pkl'
    joblib.dump(model, model_file)
    print(f"\n💾 Model saved: {model_file}")
    
    # Save feature names
    features_file = MODELS_DIR / 'feature_names.pkl'
    joblib.dump(X_train.columns.tolist(), features_file)
    print(f"💾 Features saved: {features_file}")

def log_experiment(metrics, hyperparams):
    """Log experiment metrics and parameters to JSON (experiment tracking)"""
    mlruns_dir = Path(__file__).parent.parent / 'mlruns'
    mlruns_dir.mkdir(exist_ok=True)
    
    experiment_log = {
        'timestamp': datetime.now().isoformat(),
        'experiment': 'E-Commerce Ad Click Prediction',
        'hyperparameters': hyperparams,
        'metrics': metrics
    }
    
    # Save to mlruns/experiment_log.jsonl (append mode)
    log_file = mlruns_dir / 'experiment_log.jsonl'
    with open(log_file, 'a') as f:
        f.write(json.dumps(experiment_log) + '\n')
    
    print(f"📊 Experiment logged to: {log_file}")

def run_training_pipeline():
    """Execute full training pipeline with experiment tracking"""
    print("🚀 Random Forest Training Pipeline\n")
    
    # Load
    df = load_processed_data()
    
    # Prepare
    X, y = prepare_features_target(df)
    
    # Train
    model, X_train, X_test, y_train, y_test = train_random_forest(X, y)
    
    # Evaluate
    metrics = evaluate_model(model, X_train, X_test, y_train, y_test)
    
    # Hyperparameters for logging
    hyperparams = {
        'n_estimators': 100,
        'max_depth': 15,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'test_size': 0.2,
        'random_state': 42
    }
    
    # Log experiment
    log_experiment(metrics, hyperparams)
    
    # Save model
    save_model(model, X_train)
    
    print("\n✅ Training Complete!")
    return model, metrics

if __name__ == '__main__':
    run_training_pipeline()
