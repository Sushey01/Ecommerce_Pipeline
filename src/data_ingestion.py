"""
Data Ingestion Script
Fetches ecommerce dataset from Kaggle and saves to data/ folder
"""

import os
import kaggle
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Set Kaggle credentials from environment
os.environ['KAGGLE_USERNAME'] = os.getenv('KAGGLE_USERNAME')
os.environ['KAGGLE_KEY'] = os.getenv('KAGGLE_KEY')

DATA_DIR = Path(__file__).parent.parent / 'data'
DATASET_NAME = 'asifxzaman/e-commerce-behavior-dataset8000-users'

def download_dataset():
    """Download dataset from Kaggle"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"📥 Downloading dataset: {DATASET_NAME}")
    print(f"📂 Destination: {DATA_DIR}")
    
    try:
        kaggle.api.dataset_download_files(
            DATASET_NAME,
            path=DATA_DIR,
            unzip=True
        )
        print("✅ Dataset downloaded successfully!")
        
        # List downloaded files
        files = list(DATA_DIR.glob('*.csv'))
        print(f"📊 CSV files found: {len(files)}")
        for file in files:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   - {file.name} ({size_mb:.2f} MB)")
        
        return True
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return False

if __name__ == '__main__':
    download_dataset()
