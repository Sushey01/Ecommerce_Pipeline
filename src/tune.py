"""
Hyperparameter Tuning Module
Loads processed data, runs GridSearchCV, and saves best parameters
"""

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
import joblib

from src.database import read_from_db

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

def tune():
    """Run GridSearchCV to find best hyperparameters for Random Forest and save them"""
    print("🤖 Tuning Stage: Hyperparameter Tuning...")
    
    # Load processed data
    df = read_from_db("SELECT * FROM processed_ecommerce_data")
    
    # Separate features and target
    X = df.drop('ad_clicked', axis=1)
    y = df['ad_clicked']
    
    # Run Grid Search (lightweight to prevent heavy task execution in Airflow)
    param_grid = {
        'n_estimators': [10],
        'max_depth': [5]
    }
    
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    base = RandomForestClassifier(random_state=42, n_jobs=-1)
    
    print("⏱️ Running GridSearchCV...")
    gs = GridSearchCV(base, param_grid, cv=cv, scoring='roc_auc', n_jobs=-1, verbose=1)
    gs.fit(X, y)
    
    best_params = gs.best_params_
    print(f"✅ Best parameters found: {best_params}")
    
    # Save best parameters to disk
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    params_file = MODELS_DIR / 'best_params.pkl'
    joblib.dump(best_params, params_file)
    print(f"💾 Saved best parameters to: {params_file}")

if __name__ == '__main__':
    tune()
