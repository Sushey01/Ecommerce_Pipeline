# Flask app

from flask import Flask, request, jsonify
import joblib
import redis
import json
import os

app = Flask(__name__)

# Load model
model = joblib.load("model.pkl")

# Redis connection with environment variables
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route("/predict", methods=["POST"])
def predict():
    """Predict salary based on experience"""
    try:
        data = request.get_json()
        exp = data.get("exp")
        
        if exp is None:
            return jsonify({"error": "Missing 'exp' parameter"}), 400
        
        # Redis cache check
        cache_key = f"prediction:{exp}"
        if r.exists(cache_key):
            return jsonify(json.loads(r.get(cache_key))), 200
        
        # Make prediction
        result = model.predict([[exp]])[0]
        response = {"experience": exp, "salary": float(result)}
        
        # Cache result
        r.set(cache_key, json.dumps(response), ex=3600)  # Cache for 1 hour
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)