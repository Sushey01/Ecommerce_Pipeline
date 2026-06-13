"""
Transformation Module (ELT - Transform)
Loads raw data from MariaDB, processes it, and writes processed data back to MariaDB
"""

import pandas as pd
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
import joblib

from src.database import read_from_db, write_to_db

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

def transform():
    """
    Load raw data from MariaDB, preprocess it, and save back to MariaDB.
    Also saves label encoders for inference.
    """
    print("🧹 Transform Stage: Preprocessing raw MariaDB data...")
    
    # Load raw data
    print("📂 Loading raw_ecommerce_data from warehouse...")
    df = read_from_db("SELECT * FROM raw_ecommerce_data")
    print(f"📊 Raw data shape: {df.shape}")
    
    # Preprocess
    df_processed = df.copy()
    
    # Drop user_id (not a feature)
    if 'user_id' in df_processed.columns:
        df_processed = df_processed.drop('user_id', axis=1)
        
    # Handle missing values
    df_processed['gender'] = df_processed['gender'].fillna('Unknown')
    df_processed['device_type'] = df_processed['device_type'].fillna('Unknown')
    df_processed['avg_session_time'] = df_processed['avg_session_time'].fillna(df_processed['avg_session_time'].median())
    
    # Drop rows where target is missing
    df_processed = df_processed[df_processed['ad_clicked'].notna()]
    
    # Encode categorical variables
    le_gender = LabelEncoder()
    le_device = LabelEncoder()
    
    df_processed['gender'] = le_gender.fit_transform(df_processed['gender'])
    df_processed['device_type'] = le_device.fit_transform(df_processed['device_type'])
    
    # Save encoders for later use
    encoders = {
        'gender': le_gender,
        'device_type': le_device
    }
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    encoders_file = MODELS_DIR / 'encoders.pkl'
    joblib.dump(encoders, encoders_file)
    print(f"💾 Saved encoders to: {encoders_file}")
    
    # Save processed data to database
    print("💾 Saving processed data to processed_ecommerce_data table in MariaDB...")
    write_to_db(df_processed, 'processed_ecommerce_data')
    
    print("✅ Transform stage complete!")

if __name__ == '__main__':
    transform()
