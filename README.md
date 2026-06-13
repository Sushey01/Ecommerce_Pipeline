# MLOps E-Commerce Pipeline

A production-grade, containerized MLOps pipeline for data ingestion, preprocessing (ELT), hyperparameter tuning, model training, evaluation, and monitoring of an e-commerce ad click prediction model.

## Project Structure

```
mlops-ecommerce/
├── api/
│   └── app.py                 # FastAPI service for predictions and dashboards
├── dags/
│   ├── ecommerce_pipeline.py   # Airflow DAG for ML training (Extract -> Load -> Transform -> Tune -> Train -> Evaluate)
│   └── monitoring_pipeline.py  # Airflow DAG for continuous system and drift monitoring
├── src/
│   ├── database.py            # MariaDB database connection helper
│   ├── drift_detection.py     # Evidently AI data drift report generator
│   ├── evaluate.py            # Model evaluation against test splits
│   ├── extract.py             # Kaggle dataset downloader
│   ├── load.py                # Raw data loading into MariaDB
│   ├── monitoring.py          # Metric tracking and HTML dashboard rendering
│   ├── predict.py             # Model inference helper
│   ├── redis_client.py        # Redis client & caching interface
│   ├── train.py               # Model training script
│   ├── transform.py           # Preprocessing and label encoding
│   └── tune.py                # Hyperparameter tuning (GridSearchCV)
├── Dockerfile                 # Docker configuration for FastAPI web service
├── docker-compose.yml         # Multi-container service configuration
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables and API credentials
```

## Features

- **FastAPI serving endpoint**: Multi-threaded, low-latency prediction endpoint with Redis caching support.
- **Observability Dashboards**: Real-time FastAPI endpoints serving a system health `/monitoring` dashboard and an interactive Evidently AI `/drift` report.
- **Decoupled Airflow Orchestration**:
  - `ecommerce_ml_pipeline`: Automates extract, load, transform, tune, train, and evaluation steps.
  - `mlops_monitoring`: Runs in parallel to calculate data drift, extract metrics, and update system dashboards.
- **MariaDB Storage (OLTP/OLAP)**: Holds raw ingestion and processed training tables.
- **MLflow Tracking**: Logs training parameters, validation metrics, and model artifacts (`.pkl` files) automatically.
- **Dockerized Infrastructure**: Runs FastAPI, Redis, MariaDB, MLflow, and Apache Airflow in container isolation.

## Setup & Running

### Docker Setup (Production/Simulation)

1. Ensure your `.env` contains the required Kaggle credentials (if downloading datasets dynamically).
2. Start the entire container stack:
   ```bash
   docker compose up -d
   ```

   This orchestrates:
   - **FastAPI server** on `http://localhost:8005`
   - **Airflow UI** on `http://localhost:8081`
   - **MLflow Server** on `http://localhost:5002`
   - **Redis cache** on `localhost:6380` (internally 6379)
   - **MariaDB database** on `localhost:3310` (internally 3306)

3. Verify service statuses:
   ```bash
   docker compose ps
   ```

### Local Setup (Development)

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Point env vars to local ports (since Docker exposes them mapping 3310 -> 3306 and 6380 -> 6379):
   Set `DB_HOST=localhost`, `DB_PORT=3310`, `REDIS_HOST=localhost`, `REDIS_PORT=6380`, and `MLFLOW_TRACKING_URI=http://localhost:5002`.

3. Run FastAPI locally:
   ```bash
   uvicorn api.app:app --host 0.0.0.0 --port 8000
   ```

---

## API Endpoints

### 1. Health Status
* **Endpoint**: `GET http://localhost:8005/health`
* **Response**:
  ```json
  {
    "status": "healthy",
    "redis": "connected"
  }
  ```

### 2. Predict Ad Click
* **Endpoint**: `POST http://localhost:8005/predict`
* **Headers**: `Content-Type: application/json`
* **Payload**:
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
* **Response**:
  ```json
  {
    "ad_clicked_probability": 0.82,
    "ad_clicked": 1,
    "cached": false
  }
  ```
  *(Subsequent requests with identical payloads are retrieved from the Redis cache and return `"cached": true`)*

### 3. Monitoring Dashboard
* **Endpoint**: `GET http://localhost:8005/monitoring`
* **Details**: Serves an HTML page visualising MLOps latency, metrics, and execution history.

### 4. Interactive Drift Report
* **Endpoint**: `GET http://localhost:8005/drift`
* **Details**: Serves an interactive HTML report compiled by Evidently AI analyzing feature drift between current reference splits.

---

## Airflow Orchestration

1. **`ecommerce_ml_pipeline`**: Runs the complete training flow:
   - `extract`: Downloads e-commerce raw user behavior data.
   - `load`: Ingests the CSV data into MariaDB raw tables.
   - `transform`: Encodes categorical columns and writes to processed tables.
   - `tune`: Optimizes Random Forest hyperparameters via `GridSearchCV`.
   - `train`: Trains the final estimator and logs metrics to MLflow.
   - `evaluate`: Validates model metrics against held-out splits.

2. **`mlops_monitoring`**: Runs drift computation and generates HTML dashboard reports for the serving API to display.

---

## Troubleshooting

### Inspecting Container Logs
```bash
# Check if Redis is running
docker compose logs redis

# Restart Redis
docker compose restart redis
```

### Airflow Issues
```bash
# View Airflow logs
docker compose logs airflow

# Reinitialize Airflow
docker compose exec airflow airflow db init
```

### Model Training Failed
```bash
# Retrain model locally
python app/train.py
```

## Development

### Adding New Dependencies
1. Update `requirements.txt`
2. Rebuild Docker image: `docker compose build`
3. Restart services: `docker compose up -d`

### Modifying the Model
Edit `app/train.py` and run locally or trigger Airflow DAG.

## License

MIT
