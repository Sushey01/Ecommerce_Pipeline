# MLOps E-Commerce Pipeline

A production-grade, containerized MLOps pipeline for data ingestion, preprocessing (ELT), hyperparameter tuning, model training, evaluation, and monitoring of an e-commerce **ad click prediction** model.

---

## 📌 Overview

This project demonstrates a full end-to-end MLOps lifecycle:

- Data ingestion from **Kaggle**
- ELT (Extract → Load → Transform) pipeline with **MariaDB ColumnStore** as an analytical OBT warehouse
- Feature engineering, **One-Hot Encoding**, and **StandardScaler** preprocessing (fit on train set only to prevent leakage)
- **Stratified train/test split** (80/20) pushed to **Redis** as an in-memory data bus
- Multi-model comparison and hyperparameter tuning via **RandomizedSearchCV + StratifiedKFold** across Logistic Regression, Random Forest, and XGBoost
- Winning model trained and evaluated with full diagnostic plots (ROC, PR curve, Confusion Matrix)
- **Experiment tracking** with MLflow (parameters, metrics, model artifacts, plots)
- **Real-time prediction serving** using FastAPI with Redis prediction caching and background DB logging
- **Data drift monitoring** using Evidently AI (interactive HTML reports)
- **System health monitoring** with a custom HTML dashboard
- Workflow orchestration using **Apache Airflow** (two parallel DAGs)
- Fully containerized system using **Docker Compose**

---

## 🏗️ System Architecture

```text
Kaggle Dataset
      │
      ▼
┌─────────────┐
│   Extract   │  src/extract.py  ─ Downloads dataset via Kaggle API
└─────────────┘
      │
      ▼
┌─────────────┐
│    Load     │  src/load.py  ─ Ingests CSV into MariaDB raw_ecommerce_data table
└─────────────┘      │
                      ▼
              MariaDB ColumnStore
              (OBT: raw_ecommerce_data)
      │
      ▼
┌─────────────┐
│  Transform  │  src/transform.py
│             │  • Missing value imputation
│             │  • Feature engineering (engagement_score, age_discount_interaction)
│             │  • Stratified train/test split (80/20, random_state=42)
│             │  • OneHotEncoder (gender, device_type) — fit on train only
│             │  • StandardScaler (numerical cols)  — fit on train only
│             │  • Saves encoders/scaler → models/
│             │  • Writes OBT → processed_ecommerce_data (MariaDB)
│             │  • Pushes train/test splits → Redis data bus
└─────────────┘
      │
      ▼
┌──────────────────┐
│  Redis Data Bus  │  dataset:train_X / train_y / test_X / test_y
└──────────────────┘
      │
      ▼
┌─────────────┐
│    Tune     │  src/tune.py  ─ RandomizedSearchCV + StratifiedKFold (5 folds)
│             │  Models compared: LogisticRegression, RandomForest, XGBoost
│             │  Metric: ROC-AUC  |  Logs all runs to MLflow
│             │  Saves winner config → models/best_model_config.pkl
└─────────────┘
      │
      ▼
┌─────────────┐
│    Train    │  src/train.py  ─ Loads winner config, trains final model
│             │  Logs params + model artifact to MLflow
│             │  Saves → models/best_model.pkl + feature_names.pkl
└─────────────┘
      │
      ▼
┌─────────────┐
│  Evaluate   │  src/evaluate.py  ─ Accuracy, Precision, Recall, F1, ROC-AUC
│             │  Generates: roc_curve.png, pr_curve.png, confusion_matrix.png
│             │  Logs metrics + plot artifacts to MLflow
└─────────────┘
      │
      ▼
┌─────────────┐
│   MLflow    │  Experiment: "E-Commerce Ad Click Prediction"
│   Server    │  Tracks: tuning runs, final model, evaluation metrics & plots
└─────────────┘

─────────────────────────────────────────────────────────────────────

### 🚀 Serving Layer

User Request
     │
     ▼
 FastAPI  (api/app.py)
     │
     ├──▶ Redis  ─ Check prediction cache (cache hit → return immediately)
     │              Cache miss → run inference → store in Redis
     │
     ├──▶ ML Model  (models/best_model.pkl + one_hot_encoder.pkl + scaler.pkl)
     │
     └──▶ MariaDB  ─ Background task logs every request to prediction_logs table

─────────────────────────────────────────────────────────────────────

### 📊 Monitoring Layer  (runs every 5 minutes, parallel to training DAG)

Airflow mlops_monitoring DAG
        │
        ▼
  src/monitoring.py
        │
        ├──▶ System health metrics (Redis ping, DB query, container uptime)
        ├──▶ Evidently AI drift detection (reference vs. current splits)
        │         └──▶ reports/data_drift_report.html
        └──▶ HTML system dashboard
                  └──▶ reports/monitoring_dashboard.html

FastAPI /monitoring  →  serves monitoring_dashboard.html
FastAPI /drift       →  serves data_drift_report.html  (interactive Evidently AI)
```

---

## 🗂️ Project Structure

```
mlops_ecommerce/
├── api/
│   └── app.py                 # FastAPI: predictions, caching, background logging, dashboards
├── dags/
│   ├── ecommerce_pipeline.py  # Airflow DAG: ingest → preprocess → tune → train → evaluate
│   └── monitoring_pipeline.py # Airflow DAG: continuous system & drift monitoring (every 5 min)
├── src/
│   ├── database.py            # MariaDB ColumnStore connection & OBT write helper
│   ├── drift_detection.py     # Evidently AI data drift report generator
│   ├── evaluate.py            # Model evaluation: metrics + ROC/PR/CM plots → MLflow
│   ├── extract.py             # Kaggle dataset downloader
│   ├── load.py                # Raw CSV ingestion into MariaDB
│   ├── monitoring.py          # System health metrics + HTML dashboard renderer
│   ├── predict.py             # Inference helper (loads model, encoder, scaler)
│   ├── redis_client.py        # Redis client: prediction cache + dataframe data bus
│   ├── train.py               # Final model training (uses winner config from tune)
│   ├── transform.py           # Preprocessing: OHE + StandardScaler + feature engineering
│   └── tune.py                # RandomizedSearchCV across LR / RF / XGBoost
├── models/                    # Saved artifacts (auto-generated)
│   ├── best_model.pkl
│   ├── best_model_config.pkl
│   ├── feature_names.pkl
│   ├── one_hot_encoder.pkl
│   ├── scaler.pkl
│   └── reports/
│       ├── monitoring_dashboard.html
│       └── data_drift_report.html
├── figures/                   # Evaluation plots (auto-generated)
│   ├── roc_curve.png
│   ├── pr_curve.png
│   └── confusion_matrix.png
├── scripts/
│   └── make_pipeline_image.py # Utility to generate pipeline architecture diagram
├── Dockerfile                 # Docker config for FastAPI service
├── docker-compose.yml         # Multi-container service orchestration
├── start.sh                   # One-command startup script with health checks
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables & Kaggle credentials
```

---

## ✨ Key Features

| Feature | Details |
|---|---|
| **ELT Pipeline** | Extract (Kaggle API) → Load (MariaDB raw table) → Transform (preprocess + split) |
| **OBT Storage** | MariaDB ColumnStore with One Big Table pattern for both raw and processed data |
| **Leakage-Free Preprocessing** | Stratified 80/20 split done *before* fitting OHE and StandardScaler |
| **Feature Engineering** | `engagement_score = (pages_viewed × time_on_site) / (cart_items + 1)`, `age_discount_interaction` |
| **Redis Data Bus** | Train/test splits stored as `dataset:train_X/y`, `dataset:test_X/y` — consumed by tune/train/evaluate |
| **Multi-Model Tuning** | RandomizedSearchCV across Logistic Regression, Random Forest, XGBoost; scored by ROC-AUC |
| **MLflow Tracking** | Tuning runs, final training params, evaluation metrics, model `.pkl`, and diagnostic plots all logged |
| **Prediction Caching** | Redis-cached predictions; identical payloads return instantly with `"cached": true` |
| **Background DB Logging** | Every `/predict` call enqueues a background task logging request + timestamp to `prediction_logs` table |
| **Batch Predictions** | `/predict` accepts either a single object or a JSON array |
| **Monitoring DAGs** | Parallel Airflow DAG runs every 5 minutes; generates Evidently drift report + system health dashboard |
| **Dockerized Stack** | Redis, MariaDB, MLflow, FastAPI, Airflow all isolated in containers |
| **`start.sh`** | Ordered startup with Docker health checks before proceeding to next service |

---

## ⚙️ Setup & Running

### Prerequisites

- Docker & Docker Compose installed and daemon running
- Kaggle API credentials (for dataset download)

### 1. Configure environment

Create or update `.env` in the project root:

```env
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
DB_HOST=mariadb
DB_PORT=3306
DB_USER=mlops_user
DB_PASSWORD=mlops_password
DB_NAME=mlops_db
REDIS_HOST=redis
REDIS_PORT=6379
MLFLOW_TRACKING_URI=http://mlflow:5001
```

### 2. Start the full stack (recommended)

```bash
chmod +x start.sh
./start.sh
```

The `start.sh` script:
1. Validates Docker is installed and the daemon is running
2. Builds the FastAPI Docker image
3. Starts Redis & MariaDB, waits for their health checks to pass
4. Starts MLflow, then FastAPI, then Airflow (in order)
5. Prints a summary of all service URLs

### 3. Or start manually with Docker Compose

```bash
docker compose up -d
```

### 4. Verify all services are healthy

```bash
docker compose ps
```

### Service URLs

| Service | URL | Notes |
|---|---|---|
| **FastAPI** | http://localhost:8005 | Prediction & monitoring API |
| **FastAPI Docs** | http://localhost:8005/docs | Interactive Swagger UI |
| **Airflow UI** | http://localhost:8081 | Credentials: `admin` / `admin` |
| **MLflow UI** | http://localhost:5002 | Experiment tracking |
| **MariaDB** | localhost:3310 | User: `mlops_user` / `mlops_password` |
| **Redis** | localhost:6380 | Mapped from internal 6379 |

### Stopping all services

```bash
docker compose down
# Or to also remove volumes:
docker compose down -v
```

---

## 🌀 Airflow DAGs

### `ecommerce_pipeline` (runs `@daily`)

Sequential 5-stage ML training pipeline:

```
ingest_data → preprocess_data → tune_hyperparameters → train_model → evaluate_model
```

| Task | Module | What it does |
|---|---|---|
| `ingest_data` | `extract.py` + `load.py` | Downloads Kaggle dataset → loads into `raw_ecommerce_data` (MariaDB) |
| `preprocess_data` | `transform.py` | Imputes, engineers features, stratified split, fits OHE + scaler, pushes splits to Redis |
| `tune_hyperparameters` | `tune.py` | RandomizedSearchCV over LR / RF / XGBoost (5-fold StratifiedKFold, ROC-AUC), logs all runs to MLflow |
| `train_model` | `train.py` | Loads winning config, trains final model, saves `.pkl`, logs to MLflow |
| `evaluate_model` | `evaluate.py` | Accuracy, Precision, Recall, F1, ROC-AUC; saves ROC/PR/CM plots; logs metrics + artifacts to MLflow |

### `mlops_monitoring` (runs every 5 minutes)

Parallel continuous monitoring pipeline — runs independently of the training DAG:

| Task | What it does |
|---|---|
| `run_monitoring` | Collects system metrics (Redis, MariaDB health), runs Evidently AI drift detection, renders HTML dashboard and drift report to `models/reports/` |

---

## 🔌 API Endpoints

### `GET /health`
Returns service health status.

```json
{
  "status": "healthy",
  "redis": "connected"
}
```

### `POST /predict`
Predict whether a user will click an ad. Accepts a **single object** or a **JSON array** for batch inference.

**Request (single)**:
```json
{
  "age": 34.0,
  "gender": "Female",
  "device_type": "Mobile",
  "time_on_site": 14.2,
  "pages_viewed": 5.0,
  "previous_purchases": 3.0,
  "cart_items": 2.0,
  "discount_seen": 1.0,
  "returning_user": 1.0,
  "avg_session_time": 12.0,
  "bounce_rate": 0.04,
  "purchase": 1.0
}
```

**Response**:
```json
{
  "ad_clicked_probability": 0.82,
  "ad_clicked": 1,
  "cached": false
}
```

> Subsequent identical payloads return instantly from Redis cache with `"cached": true`.
> Every request is logged asynchronously to the `prediction_logs` MariaDB table (timestamp + features).

### `GET /monitoring`
Serves the **system health HTML dashboard** generated by the `mlops_monitoring` Airflow DAG. Shows MLOps latency, DB/Redis metrics, and pipeline execution history.

### `GET /drift`
Serves the **interactive Evidently AI data drift report** (HTML). Compares reference vs. current feature distributions.

### Full API documentation
Visit **http://localhost:8005/docs** for the interactive Swagger UI with all endpoint schemas.

---

## 🧠 Model Pipeline Details

### Feature Engineering (in `transform.py`)
| Feature | Formula |
|---|---|
| `engagement_score` | `(pages_viewed × time_on_site) / (cart_items + 1)` |
| `age_discount_interaction` | `age × discount_seen` |

### Preprocessing (fit on train split only)
- **OneHotEncoder**: `gender` → {Female, Male, Unknown}, `device_type` → {Desktop, Mobile, Tablet, Unknown}
- **StandardScaler**: `age`, `time_on_site`, `pages_viewed`, `previous_purchases`, `cart_items`

### Hyperparameter Search Space
| Model | Parameters |
|---|---|
| `LogisticRegression` | `C` ∈ {0.01, 0.1, 1.0, 10.0}, `solver` ∈ {liblinear, lbfgs} |
| `RandomForest` | `n_estimators` ∈ {50, 100}, `max_depth` ∈ {3, 5, 8}, `min_samples_split` ∈ {2, 5} |
| `XGBoost` | `n_estimators` ∈ {50, 100}, `max_depth` ∈ {3, 5}, `learning_rate` ∈ {0.01, 0.1} |

Cross-validation: **StratifiedKFold (5 folds)**, scored by **ROC-AUC**.

### Saved Model Artifacts
| File | Description |
|---|---|
| `models/best_model.pkl` | Trained winning classifier |
| `models/best_model_config.pkl` | Winning model type + best hyperparameters |
| `models/feature_names.pkl` | Ordered feature list for inference |
| `models/one_hot_encoder.pkl` | Fitted OHE (train split) |
| `models/scaler.pkl` | Fitted StandardScaler (train split) |

---

## 🗄️ Database Schema

| Table | Engine | Description |
|---|---|---|
| `raw_ecommerce_data` | ColumnStore (InnoDB fallback) | Raw ingested CSV data |
| `processed_ecommerce_data` | ColumnStore (InnoDB fallback) | Full OBT of preprocessed train+test data |
| `prediction_logs` | ColumnStore (InnoDB fallback) | Background-logged prediction requests with timestamps |

> MariaDB ColumnStore is used for columnar analytical performance. If the ColumnStore plugin is unavailable (e.g., local dev), the `write_to_db()` function gracefully falls back to InnoDB.

---

## 🔧 Local Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Point env vars to the Docker-exposed ports (since containers map internal → external):

```bash
export DB_HOST=localhost
export DB_PORT=3310
export REDIS_HOST=localhost
export REDIS_PORT=6380
export MLFLOW_TRACKING_URI=http://localhost:5002
```

Run FastAPI locally:

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

Run individual pipeline stages manually:

```bash
python -m src.extract
python -m src.load
python -m src.transform
python -m src.tune
python -m src.train
python -m src.evaluate
```

---

## 🐛 Troubleshooting

### Inspecting Container Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs airflow
docker compose logs web
docker compose logs mlflow
```

### Airflow Issues

```bash
# Re-initialize Airflow DB
docker compose exec airflow airflow db init

# List/trigger DAGs manually
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags trigger ecommerce_pipeline
docker compose exec airflow airflow dags trigger mlops_monitoring
```

### Model Not Found / Retrain

```bash
# Trigger the full training DAG from Airflow UI or:
docker compose exec airflow airflow dags trigger ecommerce_pipeline
```

### Redis Cache Reset

```bash
docker compose exec redis redis-cli FLUSHALL
```

### Rebuild After Dependency Changes

```bash
# Update requirements.txt, then:
docker compose build --no-cache web
docker compose up -d web
```

### Check MariaDB

```bash
docker compose exec mariadb mariadb -u mlops_user -pmlops_password mlops_db -e "SHOW TABLES;"
```

---

## 🧩 Adding New Dependencies

1. Add to `requirements.txt`
2. Add to `_PIP_ADDITIONAL_REQUIREMENTS` in `docker-compose.yml` (Airflow container)
3. Rebuild: `docker compose build --no-cache && docker compose up -d`

---

## 📦 Tech Stack

| Component | Technology |
|---|---|
| ML Framework | scikit-learn, XGBoost |
| Experiment Tracking | MLflow |
| API Server | FastAPI + Uvicorn |
| Orchestration | Apache Airflow 2.7 |
| Cache / Data Bus | Redis 7 |
| Data Warehouse | MariaDB 10.11 (ColumnStore OBT) |
| Drift Detection | Evidently AI |
| Data Validation | Great Expectations (< 1.0.0) |
| Containerization | Docker Compose |
| Data Source | Kaggle API |

---

## 📄 License

MIT
