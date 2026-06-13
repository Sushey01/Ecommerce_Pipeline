"""
Prediction Module
Loads model and handles inference logic
"""

import os
from pathlib import Path
import joblib
from typing import Tuple, Any
from fastapi import HTTPException, status

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'
MODEL_PATH = MODELS_DIR / 'random_forest_model.pkl'
ENCODERS_PATH = MODELS_DIR / 'encoders.pkl'
FEATURES_PATH = MODELS_DIR / 'feature_names.pkl'

# Lazy-loaded model resources
model = None
encoders = None
feature_names = None

def get_model_resources():
    """Load model and metadata files dynamically if not already loaded"""
    global model, encoders, feature_names
    if model is None or encoders is None or feature_names is None:
        try:
            model = joblib.load(MODEL_PATH)
            encoders = joblib.load(ENCODERS_PATH)
            feature_names = joblib.load(FEATURES_PATH)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model artifacts not available on disk. Run the training pipeline first. Error: {str(e)}"
            )
    return model, encoders, feature_names

def make_prediction(request_data: Any) -> Tuple[float, int]:
    """Preprocess request data and perform inference"""
    model_clf, enc_dict, features = get_model_resources()

    try:
        # Preprocess categories
        gender_val = request_data.gender
        if gender_val not in enc_dict['gender'].classes_:
            gender_val = 'Unknown'
        gender_encoded = int(enc_dict['gender'].transform([gender_val])[0])

        device_val = request_data.device_type
        if device_val not in enc_dict['device_type'].classes_:
            device_val = 'Unknown'
        device_encoded = int(enc_dict['device_type'].transform([device_val])[0])

        # Map request to feature vector
        features_dict = {
            'age': request_data.age,
            'gender': gender_encoded,
            'device_type': device_encoded,
            'time_on_site': request_data.time_on_site,
            'pages_viewed': request_data.pages_viewed,
            'previous_purchases': request_data.previous_purchases,
            'cart_items': request_data.cart_items,
            'discount_seen': request_data.discount_seen,
            'returning_user': request_data.returning_user,
            'avg_session_time': request_data.avg_session_time,
            'bounce_rate': request_data.bounce_rate,
            'purchase': request_data.purchase
        }

        input_vector = [features_dict[col] for col in features]

        # Perform inference
        prob = float(model_clf.predict_proba([input_vector])[0][1])
        prediction = int(model_clf.predict([input_vector])[0])

        return prob, prediction

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {str(e)}"
        )
