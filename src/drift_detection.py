"""
Evidently Drift Detection (Stable Version for Airflow + ML pipelines)
"""

from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
import pandas as pd

try:
    from evidently import Report
    from evidently.presets import DataDriftPreset
    EVIDENTLY_V1 = True
except ImportError:
    try:
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset
        EVIDENTLY_V1 = True
    except ImportError:
        try:
            from evidently.profile import Profile as Report
            from evidently.profile_sections import ProfileSection as DataDriftPreset
            EVIDENTLY_V1 = False
        except ImportError:
            # Fallback: create dummy classes if imports fail
            Report = None
            DataDriftPreset = None
            EVIDENTLY_V1 = False

from src.database import read_from_db

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
REPORTS_DIR = MODELS_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def generate_drift_report():
    """Generate a drift detection report comparing reference and current data using Evidently AI"""
    print("📈 Generating Drift Report...")

    # Load data
    try:
        df = read_from_db("SELECT * FROM processed_ecommerce_data")
    except Exception as e:
        print(f"❌ DB error: {e}")
        return

    reference_data, current_data = train_test_split(df, test_size=0.3, random_state=42)

    # Load model
    model_path = MODELS_DIR / "random_forest_model.pkl"
    if not model_path.exists():
        print("❌ Model not found")
        return

    model = joblib.load(model_path)

    # Add predictions
    X_ref = reference_data.drop("ad_clicked", axis=1)
    X_curr = current_data.drop("ad_clicked", axis=1)
    
    reference_data["prediction"] = model.predict(X_ref)
    current_data["prediction"] = model.predict(X_curr)

    # Run Evidently Report
    if Report is not None and DataDriftPreset is not None:
        try:
            print("Running Evidently DataDriftPreset Report...")
            report = Report(metrics=[
                DataDriftPreset(),
            ])
            snapshot = report.run(reference_data=reference_data, current_data=current_data)
            
            report_path = REPORTS_DIR / "data_drift_report.html"
            snapshot.save_html(str(report_path))
            print(f"✅ Interactive Evidently report saved: {report_path}")
            
            # Parse the metrics from snapshot to build the drift_summary dictionary
            snapshot_dict = snapshot.dict()
            drift_summary = []
            
            for metric in snapshot_dict.get("metrics", []):
                config = metric.get("config", {})
                if config.get("type") == "evidently:metric_v2:ValueDrift":
                    col = config.get("column")
                    threshold = config.get("threshold", 0.05)
                    p_value = metric.get("value")
                    
                    is_drift = False
                    if p_value is not None:
                        is_drift = p_value < threshold
                        
                    ref_mean = float(reference_data[col].mean()) if col in reference_data else 0.0
                    curr_mean = float(current_data[col].mean()) if col in current_data else 0.0
                    mean_diff = abs(curr_mean - ref_mean)
                    
                    drift_summary.append({
                        "feature": col,
                        "ref_mean": ref_mean,
                        "curr_mean": curr_mean,
                        "mean_diff": mean_diff,
                        "drift_detected": is_drift
                    })
            
            return drift_summary
            
        except Exception as e:
            print(f"⚠️ Evidently interactive report run failed: {e}. Falling back to basic summary.")
            
    # Fallback to basic drift detection summary if Evidently is not working
    print("\n📊 Comparing Feature Distributions (Fallback):")
    print("-" * 60)
    
    feature_cols = [col for col in reference_data.columns if col not in ["ad_clicked", "prediction"]]
    drift_summary = []
    
    for col in feature_cols:
        ref_mean = reference_data[col].mean()
        curr_mean = current_data[col].mean()
        mean_diff = abs(curr_mean - ref_mean)
        
        ref_std = reference_data[col].std()
        
        is_drift = mean_diff > (0.1 * ref_std) if ref_std > 0 else False
        
        drift_summary.append({
            "feature": col,
            "ref_mean": ref_mean,
            "curr_mean": curr_mean,
            "mean_diff": mean_diff,
            "drift_detected": is_drift
        })
        
        status = "⚠️ DRIFT" if is_drift else "✓ OK"
        print(f"{col:20} | Ref Mean: {ref_mean:8.2f} | Curr Mean: {curr_mean:8.2f} | {status}")

    # Generate basic HTML report fallback
    html_content = _generate_html_report(drift_summary, reference_data, current_data)
    
    report_path = REPORTS_DIR / "data_drift_report.html"
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"\n✅ Basic fallback drift report saved: {report_path}")
    return drift_summary



def _generate_html_report(drift_summary, reference_data, current_data):
    """Generate a simple HTML drift report"""
    html = """
    <html>
    <head>
        <title>Data Drift Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .drift {{ background-color: #ffcccc; }}
            .ok {{ background-color: #ccffcc; }}
            .summary {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>📊 Data Drift Detection Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Reference Dataset Size:</strong> {} records</p>
            <p><strong>Current Dataset Size:</strong> {} records</p>
        </div>
        
        <h2>Feature-wise Drift Analysis</h2>
        <table>
            <tr>
                <th>Feature</th>
                <th>Reference Mean</th>
                <th>Current Mean</th>
                <th>Difference</th>
                <th>Status</th>
            </tr>
    """.format(len(reference_data), len(current_data))
    
    for item in drift_summary:
        status_class = "drift" if item["drift_detected"] else "ok"
        status_text = "⚠️ DRIFT DETECTED" if item["drift_detected"] else "✓ No Drift"
        html += f"""
            <tr class="{status_class}">
                <td>{item['feature']}</td>
                <td>{item['ref_mean']:.4f}</td>
                <td>{item['curr_mean']:.4f}</td>
                <td>{item['mean_diff']:.4f}</td>
                <td>{status_text}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>Dataset Statistics</h2>
        <h3>Reference Dataset</h3>
        <pre>{}</pre>
        
        <h3>Current Dataset</h3>
        <pre>{}</pre>
        
        <p><em>Report generated by MLOps E-Commerce Pipeline</em></p>
    </body>
    </html>
    """.format(
        reference_data.describe().to_string(),
        current_data.describe().to_string()
    )
    
    return html


if __name__ == "__main__":
    generate_drift_report()