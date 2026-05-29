<<<<<<< HEAD
# DMLOPS_Ecommerce_Pipeline
=======
# MLOps E-Commerce Pipeline

A complete MLOps pipeline for e-commerce data processing, model training, and serving predictions.

## Project Structure

```
mlops-ecommerce/
├── app/
│   ├── app.py           # Flask API for predictions
│   ├── train.py         # Model training script
│   └── model.pkl        # Trained model
├── airflow/
│   └── dags/
│       └── pipeline.py  # Airflow DAG for orchestration
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-container setup
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables
```

## Features

- **Flask API**: RESTful endpoint for model predictions with Redis caching
- **ML Model**: Linear regression trained on experience/salary data
- **Redis Caching**: Cache predictions for improved performance
- **Airflow DAG**: Daily model retraining pipeline
- **Docker**: Containerized deployment with Redis and Airflow services

## Setup

### Local Setup (Development)

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Train model**:
   ```bash
   python app/train.py
   ```

4. **Run Flask app**:
   ```bash
   python -m flask run --app app/app.py
   ```

### Docker Setup (Production)

1. **Build and run with Docker Compose**:
   ```bash
   docker compose up -d
   ```

   This starts:
   - **Flask API** on `http://localhost:5000`
   - **Airflow** on `http://localhost:8080`
   - **Redis** on `localhost:6379`

2. **Check status**:
   ```bash
   docker compose ps
   ```

## API Endpoints

### Health Check
```bash
curl http://localhost:5000/health
```
**Response**: `{"status": "healthy"}`

### Predict
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"exp": 5}'
```
**Response**: `{"experience": 5, "salary": 70000.0}`

## Airflow DAG

The DAG `ml_pipeline` runs daily to:
- Train the ML model
- Update predictions cache

**Access Airflow UI**: `http://localhost:8080`

## Dependencies

- Flask 3.0.0+
- scikit-learn 1.3.0+
- Redis 5.0.0+
- Apache Airflow 2.7.0+
- pandas, numpy, joblib

See `requirements.txt` for full list.

## Troubleshooting

### Redis Connection Error
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
>>>>>>> master
