# 📚 MLOps Project - Code Structure & Study Guide

## Quick Reference Map

### Files to Study (in order):

1. **`.env`** (Credentials)
   - Where: `/home/shekhar/mlops_ecommerce/.env`
   - What: API keys and configuration
   - Contains: `KAGGLE_USERNAME`, `KAGGLE_KEY`

2. **`src/data_ingestion.py`** (Data Fetching)
   - Main function: `download_dataset()`
   - Line 6-15: API key loading (`load_dotenv()`)
   - Line 20-50: Download logic
   - How to run: `python src/data_ingestion.py`

3. **`src/preprocessing.py`** (ETL Pipeline)
   - Main function: `run_etl_pipeline()`
   - Line 39+: Main pipeline
   - Calls: `load_raw_data()`, `preprocess_data()`, `save_processed_data()`
   - How to run: `python src/preprocessing.py`

4. **`src/train_model.py`** (Model Training)
   - Main function: `run_training_pipeline()`
   - Line 82+: Training logic
   - Output: Trained model in `models/random_forest_model.pkl`
   - How to run: `python src/train_model.py`

5. **`src/generate_eda.py`** (Visualizations)
   - Generates plots to `figures/` folder
   - 6 PNG files created
   - How to run: `python src/generate_eda.py`

6. **`dags/ecommerce_pipeline.py`** ⭐ (Orchestration - THE MAIN FILE)
   - Line 12-19: Imports functions from `src/`
   - Line 36-66: Defines 3 tasks
   - Line 64-66: Sets dependencies (order of execution)
   - How to run: `airflow dags test ecommerce_ml_pipeline`

---

## Function Call Flow

```
.env (Credentials)
  ↓
  ├─→ load_dotenv() in src/data_ingestion.py
  │   ├─ Reads: KAGGLE_USERNAME, KAGGLE_KEY
  │   └─ Calls: download_dataset()
  │       └─ Output: data/ecommerce_user_behavior_8000.csv
  │
  ├─→ src/preprocessing.py
  │   ├─ Calls: run_etl_pipeline()
  │   └─ Output: models/processed_data.csv
  │
  ├─→ src/train_model.py
  │   ├─ Calls: run_training_pipeline()
  │   └─ Output: models/random_forest_model.pkl
  │
  └─→ src/generate_eda.py
      └─ Output: figures/*.png
```

---

## Key Concepts Explained

### `load_dotenv()`
- Reads the `.env` file and loads variables into `os.environ`
- Makes credentials secure (not hardcoded in scripts)

### `os.getenv('KEY')`
- Gets value of environment variable
- Returns `None` if key doesn't exist

### `if __name__ == '__main__':`
- Code block that runs only when script is executed directly
- Example: `python src/data_ingestion.py` runs this block

### `sys.path.insert(0, path)`
- Adds directory to Python search path
- Allows importing modules from custom locations

### `from X import Y`
- Imports function `Y` from module `X`
- Example: `from data_ingestion import download_dataset`

### `task_a >> task_b` (Airflow)
- Sets dependency: task_b depends on task_a
- Ensures task_b runs only after task_a completes

---

## How to Run

### Option 1: Run Individual Scripts
```bash
cd /home/shekhar/mlops_ecommerce
source venv/bin/activate

# Step 1: Fetch data (uses API key from .env)
python src/data_ingestion.py

# Step 2: Preprocess data
python src/preprocessing.py

# Step 3: Train model
python src/train_model.py

# Step 4: Generate visualizations
python src/generate_eda.py
```

### Option 2: Automated with Airflow
```bash
source venv/bin/activate
airflow dags test ecommerce_ml_pipeline
```

---

## File Dependencies

```
.env
  ↓ (read by)
data_ingestion.py
  ↓ (output: data/*.csv)
preprocessing.py
  ↓ (output: models/processed_data.csv)
train_model.py
  ↓ (output: models/*.pkl)
generate_eda.py
```

---

## Main Files Overview

| File | Purpose | Entry Point |
|------|---------|------------|
| `.env` | Store credentials | Manual creation |
| `src/data_ingestion.py` | Fetch from Kaggle | `download_dataset()` |
| `src/preprocessing.py` | ETL pipeline | `run_etl_pipeline()` |
| `src/train_model.py` | Model training | `run_training_pipeline()` |
| `src/generate_eda.py` | Visualizations | Direct execution |
| `dags/ecommerce_pipeline.py` | Orchestration | Airflow DAG |

---

## Where to Find Things

- **API Key**: `.env` file (lines 16-18)
- **Data download logic**: `src/data_ingestion.py` (lines 20-50)
- **Preprocessing logic**: `src/preprocessing.py` (lines 39+)
- **Model training**: `src/train_model.py` (lines 82+)
- **Visualization code**: `src/generate_eda.py` (entire file)
- **Orchestration**: `dags/ecommerce_pipeline.py` (lines 36-66)

---

## Study Checklist

- [ ] Open `.env` and see credentials
- [ ] Read `src/data_ingestion.py` and understand `load_dotenv()`
- [ ] Read `src/preprocessing.py` and understand ETL steps
- [ ] Read `src/train_model.py` and understand model training
- [ ] Read `src/generate_eda.py` and understand plotting
- [ ] Read `dags/ecommerce_pipeline.py` and understand orchestration
- [ ] Run `python src/data_ingestion.py` and see it fetch data
- [ ] Run `python src/preprocessing.py` and see it process data
- [ ] Run `python src/train_model.py` and see it train model
- [ ] Run `python src/generate_eda.py` and see visualizations
