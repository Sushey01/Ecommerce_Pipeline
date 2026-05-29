"""
ETL & Preprocessing Module
Cleans, transforms, and prepares data for Random Forest model
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
import joblib

DATA_DIR = Path(__file__).parent.parent / 'data'
MODELS_DIR = Path(__file__).parent.parent / 'models'

def load_raw_data():
    """Load raw CSV data"""
    csv_file = list(DATA_DIR.glob('*.csv'))[0]
    print(f"📂 Loading: {csv_file.name}")
    df = pd.read_csv(csv_file)
    print(f"📊 Shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    return df

def inspect_data(df):
    """Show data quality issues"""
    print("\n🔍 Data Quality Report:")
    print(f"Missing values:\n{df.isnull().sum()}")
    print(f"\nData types:\n{df.dtypes}")
    print(f"\nTarget distribution:\n{df['ad_clicked'].value_counts(dropna=False)}")

def preprocess_data(df):
    """
    Clean and prepare data for modeling
    """
    df = df.copy()
    
    # Drop user_id (not a feature)
    df = df.drop('user_id', axis=1)
    
    # Handle missing values
    df['gender'] = df['gender'].fillna('Unknown')
    df['device_type'] = df['device_type'].fillna('Unknown')
    df['avg_session_time'] = df['avg_session_time'].fillna(df['avg_session_time'].median())
    
    # Drop rows where target is missing
    df = df[df['ad_clicked'].notna()]
    
    # Encode categorical variables
    le_gender = LabelEncoder()
    le_device = LabelEncoder()
    
    df['gender'] = le_gender.fit_transform(df['gender'])
    df['device_type'] = le_device.fit_transform(df['device_type'])
    
    # Save encoders for later use
    encoders = {
        'gender': le_gender,
        'device_type': le_device
    }
    
    print(f"\n✅ After preprocessing: {df.shape}")
    print(f"   Missing values: {df.isnull().sum().sum()}")
    print(f"   Target: {df['ad_clicked'].value_counts().to_dict()}")
    
    return df, encoders

def save_processed_data(df, encoders):
    """Save preprocessed data and encoders"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save data
    data_file = MODELS_DIR / 'processed_data.csv'
    df.to_csv(data_file, index=False)
    print(f"💾 Saved: {data_file}")
    
    # Save encoders
    encoders_file = MODELS_DIR / 'encoders.pkl'
    joblib.dump(encoders, encoders_file)
    print(f"💾 Saved: {encoders_file}")
    
    return data_file

def run_etl_pipeline():
    """Execute full ETL pipeline"""
    print("🚀 Starting ETL Pipeline...\n")
    
    # Load
    df = load_raw_data()
    inspect_data(df)
    
    # Transform
    df_processed, encoders = preprocess_data(df)
    
    # Load
    save_processed_data(df_processed, encoders)
    
    print("\n✅ ETL Pipeline Complete!")
    return df_processed, encoders

if __name__ == '__main__':
    run_etl_pipeline()
