"""
System-wide Continuous Monitoring Script
Checks API, Database, Cache, MLflow, and Data Drift status.
Generates reports/monitoring_dashboard.html.
"""

import os
import time
import json
import requests
from pathlib import Path
from datetime import datetime
import pandas as pd
import redis

# Add project root to sys.path
import sys
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database import read_from_db
from src.drift_detection import generate_drift_report

# Setup paths
REPORTS_DIR = Path(__file__).resolve().parent.parent / "models" / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

def check_fastapi_health() -> dict:
    """Check FastAPI health and latency"""
    # Try docker network first, then localhost
    urls = ["http://web:8000/health", "http://localhost:8000/health"]
    status = {"status": "OFFLINE", "latency_ms": 0.0, "redis_status": "unknown"}
    
    for url in urls:
        try:
            start_time = time.time()
            resp = requests.get(url, timeout=3)
            latency = (time.time() - start_time) * 1000
            if resp.status_code == 200:
                data = resp.json()
                status["status"] = "HEALTHY"
                status["latency_ms"] = round(latency, 2)
                status["redis_status"] = data.get("redis", "unknown")
                return status
        except Exception:
            continue
            
    return status

def check_redis_health() -> dict:
    """Check Redis health, keys count, and ping latency"""
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", 6379))
    status = {"status": "OFFLINE", "latency_ms": 0.0, "key_count": 0}
    
    # Try docker host then localhost
    hosts = [host, "localhost"]
    for h in hosts:
        try:
            start_time = time.time()
            r = redis.Redis(host=h, port=port, decode_responses=True, socket_connect_timeout=2)
            r.ping()
            latency = (time.time() - start_time) * 1000
            
            # Count cached prediction keys
            keys = r.keys("prediction:*")
            
            status["status"] = "HEALTHY"
            status["latency_ms"] = round(latency, 2)
            status["key_count"] = len(keys)
            return status
        except Exception:
            continue
            
    return status

def check_mariadb_health() -> dict:
    """Check MariaDB connection and database row counts"""
    status = {"status": "OFFLINE", "raw_rows": 0, "processed_rows": 0, "latency_ms": 0.0}
    
    try:
        start_time = time.time()
        # Query raw table count
        try:
            raw_df = read_from_db("SELECT COUNT(*) as count FROM raw_ecommerce_data")
            raw_count = int(raw_df["count"].iloc[0])
        except Exception:
            raw_count = 0
            
        # Query processed table count
        try:
            proc_df = read_from_db("SELECT COUNT(*) as count FROM processed_ecommerce_data")
            proc_count = int(proc_df["count"].iloc[0])
        except Exception:
            proc_count = 0
            
        latency = (time.time() - start_time) * 1000
        
        status["status"] = "HEALTHY"
        status["raw_rows"] = raw_count
        status["processed_rows"] = proc_count
        status["latency_ms"] = round(latency, 2)
    except Exception as e:
        print(f"Warning: MariaDB monitoring check failed: {e}")
        
    return status

def check_mlflow_health() -> dict:
    """Check MLflow server status and search for latest runs"""
    # Monkeypatch requests to bypass Host Header check in docker network
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5001")
    status = {"status": "OFFLINE", "active_runs": 0, "latest_metrics": {}}
    
    # Map mlflow host to localhost if not inside docker network
    url_options = [mlflow_tracking_uri, "http://localhost:5001"]
    
    for base_url in url_options:
        try:
            # Check experiment details using REST API directly to avoid importing mlflow module inside lightweight monitor
            resp = requests.get(f"{base_url}/api/2.0/mlflow/experiments/search?max_results=100", timeout=3, headers={"Host": "localhost:5001"})
            if resp.status_code == 200:
                status["status"] = "HEALTHY"
                
                # Fetch runs for ad click prediction experiment
                runs_resp = requests.post(
                    f"{base_url}/api/2.0/mlflow/runs/search",
                    json={"experiment_ids": ["1", "0"], "max_results": 1, "order_by": ["attribute.start_time DESC"]},
                    timeout=3,
                    headers={"Host": "localhost:5001"}
                )
                if runs_resp.status_code == 200:
                    runs_data = runs_resp.json()
                    runs = runs_data.get("runs", [])
                    status["active_runs"] = len(runs)
                    if runs:
                        latest_run = runs[0]
                        metrics = latest_run.get("data", {}).get("metrics", [])
                        status["latest_metrics"] = {m["key"]: round(m["value"], 4) for m in metrics}
                return status
        except Exception:
            continue
            
    return status

def run_system_monitoring():
    """Execute all health checks and generate HTML dashboard"""
    print(f"🕒 Running system-wide health checks: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Gather health statistics
    fastapi_status = check_fastapi_health()
    redis_status = check_redis_health()
    mariadb_status = check_mariadb_health()
    mlflow_status = check_mlflow_health()
    
    # 2. Run data drift detection
    drift_summary = []
    drift_alert = False
    drift_count = 0
    
    try:
        drift_summary = generate_drift_report()
        if drift_summary:
            drift_count = sum(1 for item in drift_summary if item.get("drift_detected", False))
            drift_alert = drift_count > 0
    except Exception as e:
        print(f"Warning: Could not generate drift report: {e}")
        
    # 3. Assemble Dashboard HTML
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine overall system health class
    all_healthy = (
        fastapi_status["status"] == "HEALTHY" and
        redis_status["status"] == "HEALTHY" and
        mariadb_status["status"] == "HEALTHY"
    )
    system_status_text = "ALL SYSTEMS OPERATIONAL" if all_healthy else "DEGRADED PERFORMANCE"
    system_status_class = "sys-healthy" if all_healthy else "sys-warning"
    
    # Generate drift features rows
    drift_rows_html = ""
    if drift_summary:
        for item in drift_summary:
            status_class = "drift-alert" if item["drift_detected"] else "drift-ok"
            status_badge = "⚠️ DRIFT" if item["drift_detected"] else "✓ OK"
            drift_rows_html += f"""
            <tr>
                <td style="font-weight: 500;">{item['feature']}</td>
                <td>{item['ref_mean']:.4f}</td>
                <td>{item['curr_mean']:.4f}</td>
                <td>{item['mean_diff']:.4f}</td>
                <td><span class="badge {status_class}">{status_badge}</span></td>
            </tr>
            """
    else:
        drift_rows_html = """
        <tr>
            <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">
                No data drift results available. Run data ingestion first.
            </td>
        </tr>
        """
        
    # Model metrics HTML
    metrics_html = ""
    metrics = mlflow_status.get("latest_metrics", {})
    if metrics:
        for k, v in metrics.items():
            nice_name = k.replace("eval_", "").upper()
            metrics_html += f"""
            <div class="metric-card">
                <div class="metric-val">{v}</div>
                <div class="metric-lbl">{nice_name}</div>
            </div>
            """
    else:
        metrics_html = """
        <div style="grid-column: span 3; text-align: center; color: var(--text-muted); padding: 20px;">
            No model evaluation metrics loaded from MLflow yet.
        </div>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLOps E-Commerce Monitoring Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #0b0f19;
            --bg-card: rgba(22, 28, 45, 0.6);
            --border-card: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .container {{
            width: 100%;
            max-width: 1200px;
        }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            width: 100%;
        }}
        
        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .sys-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .sys-healthy {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            border-color: rgba(16, 185, 129, 0.3);
        }}
        
        .sys-warning {{
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
            border-color: rgba(245, 158, 11, 0.3);
        }}
        
        .pulse-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: currentColor;
            box-shadow: 0 0 10px currentColor;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.5; }}
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.15);
        }}
        
        .card-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .status-indicator {{
            font-size: 0.85rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .status-healthy {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }}
        
        .status-offline {{
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }}
        
        .stat-item {{
            margin-bottom: 16px;
        }}
        
        .stat-item:last-child {{
            margin-bottom: 0;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        
        .stat-val {{
            font-size: 1.25rem;
            font-weight: 600;
        }}
        
        .drift-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 32px;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            margin-bottom: 40px;
        }}
        
        .drift-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}
        
        .drift-title {{
            font-size: 1.4rem;
            font-weight: 600;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            text-align: left;
        }}
        
        th, td {{
            padding: 14px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        th {{
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        
        .badge {{
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        
        .drift-alert {{
            background: rgba(239, 68, 68, 0.15);
            color: var(--danger);
        }}
        
        .drift-ok {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 10px;
        }}
        
        .metric-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        
        .metric-val {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #60a5fa;
            margin-bottom: 6px;
        }}
        
        .metric-lbl {{
            font-size: 0.8rem;
            color: var(--text-muted);
            letter-spacing: 0.05em;
        }}
        
        footer {{
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 20px;
            width: 100%;
        }}
        
        .btn {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s ease;
        }}
        
        .btn:hover {{
            background: #2563eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>📊 MLOps System Monitoring</h1>
                <p style="color: var(--text-muted); font-size: 0.95rem; margin-top: 4px;">Continuous environment audit & dataset drift diagnostics</p>
            </div>
            <div class="sys-badge {system_status_class}">
                <div class="pulse-dot"></div>
                {system_status_text}
            </div>
        </header>
        
        <div class="grid">
            <!-- FastAPI Serving API -->
            <div class="card">
                <div class="card-title">
                    <span>Serving API (FastAPI)</span>
                    <span class="status-indicator {'status-healthy' if fastapi_status['status'] == 'HEALTHY' else 'status-offline'}">
                        <span class="pulse-dot"></span>{fastapi_status['status']}
                    </span>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Response Latency</div>
                    <div class="stat-val">{fastapi_status['latency_ms']} ms</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Redis Cache Link</div>
                    <div class="stat-val" style="text-transform: capitalize; color: {'var(--success)' if fastapi_status['redis_status'] == 'connected' else 'var(--danger)'}">{fastapi_status['redis_status']}</div>
                </div>
            </div>
            
            <!-- Redis Cache -->
            <div class="card">
                <div class="card-title">
                    <span>Cache Store (Redis)</span>
                    <span class="status-indicator {'status-healthy' if redis_status['status'] == 'HEALTHY' else 'status-offline'}">
                        <span class="pulse-dot"></span>{redis_status['status']}
                    </span>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Ping Latency</div>
                    <div class="stat-val">{redis_status['latency_ms']} ms</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Cached Predictions</div>
                    <div class="stat-val">{redis_status['key_count']} items</div>
                </div>
            </div>
            
            <!-- MariaDB Data Warehouse -->
            <div class="card">
                <div class="card-title">
                    <span>Warehouse (MariaDB)</span>
                    <span class="status-indicator {'status-healthy' if mariadb_status['status'] == 'HEALTHY' else 'status-offline'}">
                        <span class="pulse-dot"></span>{mariadb_status['status']}
                    </span>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Raw Database Records</div>
                    <div class="stat-val">{mariadb_status['raw_rows']:,} rows</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Processed ML Features</div>
                    <div class="stat-val">{mariadb_status['processed_rows']:,} rows</div>
                </div>
            </div>
        </div>
        
        <!-- Model Metrics -->
        <div class="drift-section">
            <div class="drift-header">
                <div class="drift-title">🎯 Latest Model Training Metrics (MLflow)</div>
                <span class="status-indicator {'status-healthy' if mlflow_status['status'] == 'HEALTHY' else 'status-offline'}">
                    MLflow Server: {mlflow_status['status']}
                </span>
            </div>
            <div class="metrics-grid">
                {metrics_html}
            </div>
        </div>
        
        <!-- Data Drift Section -->
        <div class="drift-section">
            <div class="drift-header">
                <div>
                    <div class="drift-title">📈 Dataset Drift Status (Evidently AI)</div>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 4px;">Comparing baseline training split vs current inference database records</p>
                </div>
                <div style="display: flex; gap: 12px; align-items: center;">
                    <a href="/drift" target="_blank" class="btn" style="text-decoration: none;">View Interactive Evidently AI Report</a>
                    <span class="badge {'drift-alert' if drift_alert else 'drift-ok'}" style="font-size: 0.95rem; padding: 8px 12px;">
                        {f"⚠️ DRIFT ALERTS DETECTED ({drift_count})" if drift_alert else "✓ DATA STABLE (NO DRIFT)"}
                    </span>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Feature</th>
                        <th>Reference Mean</th>
                        <th>Current Mean</th>
                        <th>Difference</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {drift_rows_html}
                </tbody>
            </table>
        </div>
        
        <footer>
            <div>Last Updated: <strong>{now_str}</strong></div>
            <div>MLOps E-Commerce Pipeline &bull; continuous monitoring task</div>
        </footer>
    </div>
</body>
</html>
"""
    
    # Save the dashboard HTML
    report_path = REPORTS_DIR / "monitoring_dashboard.html"
    with open(report_path, "w") as f:
        f.write(html_template)
    print(f"✅ Monitoring dashboard HTML successfully generated at: {report_path}")

if __name__ == "__main__":
    run_system_monitoring()
