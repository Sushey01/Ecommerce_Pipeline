"""
Prediction Module
Loads best trained model and handles preprocessor pipeline inference logic
"""

import os
from pathlib import Path
import joblib
from typing import Tuple, Any
from fastapi import HTTPException, status

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'
MODEL_PATH = MODELS_DIR / 'best_model.pkl'
SCALER_PATH = MODELS_DIR / 'scaler.pkl'
OHE_PATH = MODELS_DIR / 'one_hot_encoder.pkl'
FEATURES_PATH = MODELS_DIR / 'feature_names.pkl'

# Lazy-loaded model resources
model = None
scaler = None
ohe = None
feature_names = None

def get_model_resources():
    """Load model and preprocessing metadata files dynamically if not already loaded"""
    global model, scaler, ohe, feature_names
    if model is None or scaler is None or ohe is None or feature_names is None:
        try:
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            ohe = joblib.load(OHE_PATH)
            feature_names = joblib.load(FEATURES_PATH)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model artifacts not available on disk. Run the training pipeline first. Error: {str(e)}"
            )
    return model, scaler, ohe, feature_names

def make_prediction(request_data: Any) -> Tuple[float, int]:
    """Preprocess request data and perform inference"""
    model_clf, scaler_obj, ohe_obj, features = get_model_resources()

    try:
        # 1. Feature engineering (using raw values)
        age = request_data.age
        time_on_site = request_data.time_on_site
        pages_viewed = request_data.pages_viewed
        previous_purchases = request_data.previous_purchases
        cart_items = request_data.cart_items
        discount_seen = request_data.discount_seen
        gender = request_data.gender or 'Unknown'
        device_type = request_data.device_type or 'Unknown'
        
        engagement_score = (pages_viewed * time_on_site) / (cart_items + 1)
        age_discount_interaction = age * discount_seen
        
        # 2. Scale continuous features
        scaled_nums = scaler_obj.transform([[age, time_on_site, pages_viewed, previous_purchases, cart_items]])[0]
        
        # 3. One-hot encode categorical features
        ohe_cats = ohe_obj.transform([[gender, device_type]])[0]
        ohe_feature_names = [f"{col}_{cat}" for col, cats in zip(['gender', 'device_type'], ohe_obj.categories_) for cat in cats]
        
        # Build dictionary of all features
        features_dict = {
            'age': scaled_nums[0],
            'time_on_site': scaled_nums[1],
            'pages_viewed': scaled_nums[2],
            'previous_purchases': scaled_nums[3],
            'cart_items': scaled_nums[4],
            'discount_seen': discount_seen,
            'engagement_score': engagement_score,
            'age_discount_interaction': age_discount_interaction
        }
        
        # Add OHE features
        for f_name, f_val in zip(ohe_feature_names, ohe_cats):
            features_dict[f_name] = f_val
            
        # Construct input vector in correct feature names order
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

