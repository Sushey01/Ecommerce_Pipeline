"""
FastAPI application
Serves predictions via REST API using modular components
"""

from fastapi import FastAPI, status, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Union, List


# Ensure src is in python path
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from predict import make_prediction
from redis_client import get_redis_client, get_cached_prediction, set_cached_prediction

app = FastAPI(
    title="MLOps E-Commerce Ad Click Prediction API",
    description="FastAPI service for serving Random Forest predictions with Redis caching",
    version="1.0.0"
)

# ── Serve React frontend build ────────────────────────────────
_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST / "assets")), name="assets")

@app.get("/", response_class=FileResponse, include_in_schema=False)
def frontend_root():
    """Serve the React SPA index.html"""
    index = _DIST / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return HTMLResponse("<h2>Frontend not built. Run <code>npm run build</code> in the frontend/ directory.</h2>", status_code=503)

# Initialize Redis client on startup
r = get_redis_client()

class PredictionRequest(BaseModel):
    age: float = Field(..., description="Age of the user")
    gender: str = Field("Unknown", description="Gender (Female, Male, Unknown)")
    device_type: str = Field("Unknown", description="Device type (Desktop, Mobile, Tablet, Unknown)")
    time_on_site: float = Field(..., description="Time spent on site in minutes")
    pages_viewed: float = Field(..., description="Number of pages viewed")
    previous_purchases: float = Field(..., description="Number of previous purchases")
    cart_items: float = Field(..., description="Number of items in the cart")
    discount_seen: float = Field(..., description="Whether user saw discount (1.0 or 0.0)")
    returning_user: float = Field(..., description="Whether user is a returning user (1.0 or 0.0)")
    avg_session_time: float = Field(..., description="Average session time in minutes")
    bounce_rate: float = Field(..., description="Bounce rate percentage")
    purchase: float = Field(..., description="Whether purchase was made (1.0 or 0.0)")

class PredictionResponse(BaseModel):
    ad_clicked_probability: float = Field(..., description="Probability of clicking the ad")
    ad_clicked: int = Field(..., description="Prediction (1 = click, 0 = no click)")
    cached: bool = Field(False, description="Whether prediction came from cache")

@app.get("/health", status_code=status.HTTP_200_OK)
def health():
    """Health check endpoint"""
    status_report = {"status": "healthy"}
    if r is not None:
        try:
            r.ping()
            status_report["redis"] = "connected"
        except Exception:
            status_report["redis"] = "disconnected"
    return status_report

@app.get("/monitoring", response_class=HTMLResponse)
def get_monitoring_dashboard():
    """Serve the system-wide HTML monitoring dashboard"""
    report_path = Path("/app/models/reports/monitoring_dashboard.html")
    if not report_path.exists():
        # Fallback for local development outside Docker
        report_path = Path(__file__).resolve().parent.parent / "models" / "reports" / "monitoring_dashboard.html"
        
    if report_path.exists():
        with open(report_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return HTMLResponse(
            content="""
            <html>
            <head>
                <title>Monitoring Dashboard - Not Ready</title>
                <style>
                    body { font-family: sans-serif; background-color: #0b0f19; color: #9ca3af; text-align: center; padding-top: 100px; }
                    h1 { color: #f3f4f6; }
                    .container { max-width: 600px; margin: 0 auto; border: 1px solid rgba(255,255,255,0.08); padding: 30px; border-radius: 12px; background: rgba(22,28,45,0.6); }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 MLOps System Monitoring Dashboard</h1>
                    <p>The monitoring dashboard report has not been generated yet.</p>
                    <p>Please run the monitoring script manually or wait for the Airflow <code>mlops_monitoring</code> DAG to execute.</p>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )

@app.get("/drift", response_class=HTMLResponse)
def get_drift_report():
    """Serve the interactive Evidently AI Data Drift report"""
    report_path = Path("/app/models/reports/data_drift_report.html")
    if not report_path.exists():
        # Fallback for local development outside Docker
        report_path = Path(__file__).resolve().parent.parent / "models" / "reports" / "data_drift_report.html"
        
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    else:
        return HTMLResponse(
            content="""
            <html>
            <head>
                <title>Data Drift Report - Not Ready</title>
                <style>
                    body { font-family: sans-serif; background-color: #0b0f19; color: #9ca3af; text-align: center; padding-top: 100px; }
                    h1 { color: #f3f4f6; }
                    .container { max-width: 600px; margin: 0 auto; border: 1px solid rgba(255,255,255,0.08); padding: 30px; border-radius: 12px; background: rgba(22,28,45,0.6); }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📈 Evidently AI Data Drift Report</h1>
                    <p>The interactive Evidently AI data drift report has not been generated yet.</p>
                    <p>Please run the monitoring script manually or wait for the Airflow <code>mlops_monitoring</code> DAG to execute.</p>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )


def log_prediction_requests_bg(request_data: Union[PredictionRequest, List[PredictionRequest]]):
    """Log prediction requests to prediction_logs table in MariaDB in the background"""
    try:
        from database import write_to_db
        import pandas as pd
        from datetime import datetime
        
        if isinstance(request_data, list):
            records = [item.dict() for item in request_data]
        else:
            records = [request_data.dict()]
            
        df = pd.DataFrame(records)
        df['prediction_timestamp'] = datetime.now()
        
        write_to_db(df, 'prediction_logs', if_exists='append')
    except Exception as e:
        print(f"Warning: Failed to log prediction requests to DB: {e}")

@app.post("/predict", response_model=Union[PredictionResponse, List[PredictionResponse]], status_code=status.HTTP_200_OK)
def predict(request_data: Union[PredictionRequest, List[PredictionRequest]], background_tasks: BackgroundTasks):
    """
    Predict if the user will click on an ad
    Supports either a single user object or a list of user objects.

    **Features Description (Variables metadata):**
    * **age** (metrical): float number representing user age
    * **gender** (nominal): Female, Male, Unknown
    * **device_type** (nominal): Device type (Desktop, Mobile, Tablet, Unknown)
    * **time_on_site** (metrical): float number of minutes spent on site
    * **pages_viewed** (metrical): float number of unique pages viewed
    * **previous_purchases** (metrical): float number of historical purchases
    * **cart_items** (metrical): float number of items currently in cart
    * **discount_seen** (nominal): 1.0 = Saw discount banner, 0.0 = No discount shown
    * **returning_user** (nominal): 1.0 = Returning visitor, 0.0 = New user
    * **avg_session_time** (metrical): float number of average session length in minutes
    * **bounce_rate** (metrical): bounce rate percentage value
    * **purchase** (nominal): 1.0 = Session ended in a store purchase, 0.0 = No purchase
    """
    # Enqueue background logging task
    background_tasks.add_task(log_prediction_requests_bg, request_data)

    if isinstance(request_data, list):
        results = []
        for item in request_data:
            # Check Redis cache first
            cache_key, cached_res = get_cached_prediction(r, item.dict())
            if cached_res:
                cached_res["cached"] = True
                results.append(cached_res)
                continue

            # Perform inference
            prob, prediction = make_prediction(item)
            response_dict = {
                "ad_clicked_probability": prob,
                "ad_clicked": prediction,
                "cached": False
            }
            # Cache prediction in Redis
            set_cached_prediction(r, cache_key, response_dict)
            results.append(response_dict)
        return results

    # Single prediction case
    # 1. Check Redis cache first
    cache_key, cached_res = get_cached_prediction(r, request_data.dict())
    if cached_res:
        cached_res["cached"] = True
        return cached_res

    # 2. Perform inference
    prob, prediction = make_prediction(request_data)

    response_dict = {
        "ad_clicked_probability": prob,
        "ad_clicked": prediction,
        "cached": False
    }

    # 3. Cache prediction in Redis
    set_cached_prediction(r, cache_key, response_dict)

    return response_dict

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)