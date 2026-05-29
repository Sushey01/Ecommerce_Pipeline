# 🚀 MLOps E-Commerce Pipeline - Deployment Complete ✅

## Services Running

| Service | URL | Status |
|---------|-----|--------|
| **Flask API** | http://localhost:5000 | ✅ Running |
| **Airflow** | http://localhost:8080 | ✅ Running |
| **Redis** | localhost:6379 | ✅ Running (Healthy) |

## API Testing Commands

### 1. Health Check
```bash
curl http://localhost:5000/health
```
**Response:** `{"status":"healthy"}`

### 2. Make Prediction
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"exp": 5}'
```
**Response:** `{"experience":5,"salary":70000.0}`

### 3. Test Caching (call twice, second should be cached)
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"exp": 3}'
```

### 4. Test Error Handling
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Response:** `{"error":"Missing 'exp' parameter"}`

## Docker Commands

### View Logs
```bash
# Flask app logs
docker compose logs -f web

# Airflow logs
docker compose logs -f airflow

# Redis logs
docker compose logs -f redis
```

### Stop Services
```bash
docker compose down
```

### Restart Services
```bash
docker compose up -d
```

### Check Service Health
```bash
docker compose ps
```

## Airflow DAG

Access Airflow UI: **http://localhost:8080**

Default credentials:
- Username: `airflow`
- Password: `airflow`

DAG: `ml_pipeline` - Runs daily model retraining

## What's Deployed

✅ **Flask API** - RESTful prediction endpoint with Redis caching
✅ **Redis** - In-memory cache for predictions  
✅ **Airflow** - Daily ML pipeline orchestration
✅ **Model** - Linear Regression (experience → salary)
✅ **Error Handling** - Comprehensive input validation
✅ **Health Checks** - Service health monitoring

## Next Steps

1. **Monitor API** - `docker compose logs -f web`
2. **Configure Airflow** - Visit http://localhost:8080
3. **Scale Services** - Edit docker-compose.yml for production
4. **Add Data Pipeline** - Extend with Kaggle data ingestion
5. **Add Monitoring** - Integrate MLflow/Prometheus

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | `docker compose down && docker compose up -d` |
| Flask not responding | `docker compose logs web` |
| Redis connection error | `docker compose restart redis` |
| Model version warning | Normal - model was trained with different sklearn version |

