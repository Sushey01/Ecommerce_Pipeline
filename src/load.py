import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid
import great_expectations as ge
from src.database import write_to_db

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

def load():
    """Load the raw CSV data into MariaDB data warehouse with Great Expectations validation"""
    print("🚀 Loading CSV data to MariaDB warehouse...")
    
    # Locate the CSV file
    csv_files = list(DATA_DIR.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}. Run extract task first.")
        
    csv_file = csv_files[0]
    print(f"📂 Found dataset file: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file)
        
        # Initialize Great Expectations dataset
        ge_df = ge.from_pandas(df)
        
        print("🔍 Running Great Expectations schema validation...")
        # 1. user_id is unique
        ge_df.expect_column_values_to_be_unique("user_id")
        # 2. ad_clicked is strictly 0 or 1
        ge_df.expect_column_values_to_be_in_set("ad_clicked", [0.0, 1.0, 0, 1])
        # 3. age is between 13 and 100
        ge_df.expect_column_values_to_be_between("age", 13, 100)
        
        # Identify failed rows
        # 1. Duplicated user_id
        dup_mask = df.duplicated(subset=['user_id'], keep=False)
        # 2. Invalid ad_clicked
        invalid_ad_mask = ~df['ad_clicked'].isin([0, 1])
        # 3. Invalid age
        invalid_age_mask = (df['age'] < 13) | (df['age'] > 100) | df['age'].isna()
        
        quarantine_mask = dup_mask | invalid_ad_mask | invalid_age_mask
        
        df_valid = df[~quarantine_mask].copy()
        df_quarantine = df[quarantine_mask].copy()
        
        # Generate metadata fields
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        ts_now = datetime.now()
        
        # Add metadata to valid rows
        df_valid['pipeline_run_id'] = run_id
        df_valid['ingestion_ts'] = ts_now
        
        # Write to DB
        write_to_db(df_valid, 'raw_ecommerce_data')
        print(f"✅ Successfully loaded {len(df_valid)} valid rows into raw_ecommerce_data.")
        
        if not df_quarantine.empty:
            df_quarantine['pipeline_run_id'] = run_id
            df_quarantine['ingestion_ts'] = ts_now
            # Cast ad_clicked to object so it doesn't cause type validation errors on NaNs
            df_quarantine['ad_clicked'] = df_quarantine['ad_clicked'].astype(object)
            write_to_db(df_quarantine, 'quarantine_ecommerce_data', if_exists='append')
            print(f"⚠️ Quarantined {len(df_quarantine)} invalid rows in quarantine_ecommerce_data.")
            
    except Exception as e:
        print(f"❌ Error loading data to MariaDB: {e}")
        raise e

if __name__ == '__main__':
    load()

