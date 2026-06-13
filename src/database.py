"""
Database Module
Handles connection and operations with MariaDB warehouse
"""

import os
from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    """Create and return SQLAlchemy engine for MariaDB connection"""
    host = os.getenv('DB_HOST', 'mariadb')
    port = os.getenv('DB_PORT', '3306')
    user = os.getenv('DB_USER', 'mlops_user')
    password = os.getenv('DB_PASSWORD', 'mlops_password')
    db_name = os.getenv('DB_NAME', 'mlops_db')
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(connection_string)

def write_to_db(df: pd.DataFrame, table_name: str, if_exists: str = 'replace', index: bool = False):
    """Write DataFrame to database table"""
    engine = get_db_engine()
    df.to_sql(table_name, con=engine, if_exists=if_exists, index=index)
    print(f"✅ Loaded {len(df)} rows into {table_name} table.")

def read_from_db(query: str) -> pd.DataFrame:
    """Read data from database into a DataFrame"""
    engine = get_db_engine()
    return pd.read_sql(query, con=engine)
