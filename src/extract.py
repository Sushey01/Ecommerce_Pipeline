"""
Extraction Module (ELT - Extract)
Downloads dataset from Kaggle to local data directory
"""

import os
import kaggle
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Set Kaggle credentials from environment
os.environ['KAGGLE_USERNAME'] = os.getenv('KAGGLE_USERNAME', '')
os.environ['KAGGLE_KEY'] = os.getenv('KAGGLE_KEY', '')

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DATASET_NAME = 'asifxzaman/e-commerce-behavior-dataset8000-users'

def extract():
    """Download dataset from Kaggle if not already present"""
    print("📥 Extracting dataset from Kaggle...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if CSV already exists
    existing_files = list(DATA_DIR.glob('*.csv'))
    if existing_files:
        print(f"✅ Dataset already exists locally, skipping download.")
        for file in existing_files:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   - {file.name} ({size_mb:.2f} MB)")
        return
        
    print(f"📥 Downloading dataset: {DATASET_NAME} to {DATA_DIR}")
    try:
        kaggle.api.dataset_download_files(
            DATASET_NAME,
            path=DATA_DIR,
            unzip=True
        )
        print("✅ Dataset downloaded and extracted successfully!")
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        raise e

if __name__ == '__main__':
    extract()
