"""
Loading Module (ELT - Load)
Loads raw CSV data from local data directory into MariaDB warehouse
"""

import pandas as pd
from pathlib import Path
from src.database import write_to_db

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

def load():
    """Load the raw CSV data into MariaDB data warehouse"""
    print("🚀 Loading CSV data to MariaDB warehouse...")
    
    # Locate the CSV file
    csv_files = list(DATA_DIR.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR}. Run extract task first.")
        
    csv_file = csv_files[0]
    print(f"📂 Found dataset file: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file)
        write_to_db(df, 'raw_ecommerce_data')
        print(f"✅ Successfully loaded {len(df)} rows into raw_ecommerce_data table.")
    except Exception as e:
        print(f"❌ Error loading data to MariaDB: {e}")
        raise e

if __name__ == '__main__':
    load()
