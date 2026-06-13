import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
import joblib

from src.database import read_from_db, write_to_db
from src.redis_client import get_redis_client, set_dataframe

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

def transform():
    """
    Load raw data from MariaDB, preprocess it, engineer features,
    split into train/test, and push splits to Redis.
    """
    print("🧹 Transform Stage: Preprocessing raw MariaDB data...")
    
    # Load raw data
    print("📂 Loading raw_ecommerce_data from warehouse...")
    df = read_from_db("SELECT * FROM raw_ecommerce_data")
    print(f"📊 Raw data shape: {df.shape}")
    
    # Handle missing values
    df['gender'] = df['gender'].fillna('Unknown')
    df['device_type'] = df['device_type'].fillna('Unknown')
    df['time_on_site'] = df['time_on_site'].fillna(df['time_on_site'].median())
    df['pages_viewed'] = df['pages_viewed'].fillna(df['pages_viewed'].median())
    df['previous_purchases'] = df['previous_purchases'].fillna(df['previous_purchases'].median())
    df['cart_items'] = df['cart_items'].fillna(df['cart_items'].median())
    df['discount_seen'] = df['discount_seen'].fillna(df['discount_seen'].mode()[0])
    df['age'] = df['age'].fillna(df['age'].median())
    df['avg_session_time'] = df['avg_session_time'].fillna(df['avg_session_time'].median())
    
    # Drop rows where target is missing
    df = df[df['ad_clicked'].notna()]
    
    # Feature engineering (on raw columns to prevent scaling math issues)
    df['engagement_score'] = (df['pages_viewed'] * df['time_on_site']) / (df['cart_items'] + 1)
    df['age_discount_interaction'] = df['age'] * df['discount_seen']
    
    # Define columns to keep
    target_col = 'ad_clicked'
    meta_cols = ['pipeline_run_id', 'ingestion_ts']
    num_cols = ['age', 'time_on_site', 'pages_viewed', 'previous_purchases', 'cart_items']
    cat_cols = ['gender', 'device_type']
    other_cols = ['discount_seen', 'engagement_score', 'age_discount_interaction']
    
    # Perform stratified train/test split to prevent leakage
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df[target_col])
    
    # Fit OneHotEncoder on categories
    ohe = OneHotEncoder(categories=[['Female', 'Male', 'Unknown'], ['Desktop', 'Mobile', 'Tablet', 'Unknown']],
                         handle_unknown='ignore', sparse_output=False)
    ohe.fit(train_df[cat_cols])
    ohe_feature_names = [f"{col}_{cat}" for col, cats in zip(cat_cols, ohe.categories_) for cat in cats]
    
    # Fit StandardScaler on continuous variables
    scaler = StandardScaler()
    scaler.fit(train_df[num_cols])
    
    def process_split(split_df):
        # Scale numericals
        scaled_nums = scaler.transform(split_df[num_cols])
        df_scaled = pd.DataFrame(scaled_nums, columns=num_cols, index=split_df.index)
        
        # OHE categoricals
        ohe_cats = ohe.transform(split_df[cat_cols])
        df_ohe = pd.DataFrame(ohe_cats, columns=ohe_feature_names, index=split_df.index)
        
        # Combine
        df_processed = pd.concat([
            df_scaled,
            df_ohe,
            split_df[other_cols].reset_index(drop=True).set_index(split_df.index),
            split_df[[target_col] + [c for c in meta_cols if c in split_df.columns]].reset_index(drop=True).set_index(split_df.index)
        ], axis=1)
        
        return df_processed

    train_processed = process_split(train_df)
    test_processed = process_split(test_df)
    
    # Recombine for database storage (the OBT table processed_ecommerce_data)
    df_processed_all = pd.concat([train_processed, test_processed], axis=0)
    
    # Save encoders & scaler
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(ohe, MODELS_DIR / 'one_hot_encoder.pkl')
    joblib.dump(scaler, MODELS_DIR / 'scaler.pkl')
    print(f"💾 Saved One-Hot Encoder and Scaler to: {MODELS_DIR}")
    
    # Save processed data to database
    print("💾 Saving processed data to processed_ecommerce_data table in MariaDB...")
    write_to_db(df_processed_all, 'processed_ecommerce_data')
    
    # Push splits to Redis
    r = get_redis_client()
    if r:
        print("🚀 Pushing train/test splits to Redis data bus...")
        train_X = train_processed.drop(columns=[target_col] + [c for c in meta_cols if c in train_processed.columns])
        train_y = train_processed[target_col]
        test_X = test_processed.drop(columns=[target_col] + [c for c in meta_cols if c in test_processed.columns])
        test_y = test_processed[target_col]
        
        set_dataframe(r, 'dataset:train_X', train_X)
        set_dataframe(r, 'dataset:train_y', train_y)
        set_dataframe(r, 'dataset:test_X', test_X)
        set_dataframe(r, 'dataset:test_y', test_y)
        print("✅ Successfully pushed splits to Redis.")
    else:
        print("⚠️ Redis not available. Splits will have to be loaded from DB/disk.")
        
    print("✅ Transform stage complete!")

if __name__ == '__main__':
    transform()

