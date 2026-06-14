"""
Database Module
Handles connection and operations with MariaDB ColumnStore warehouse
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# ── MariaDB ColumnStore type mapping ──────────────────────────────────────────
_DTYPE_MAP = {
    'object':   'TEXT',
    'int64':    'BIGINT',
    'int32':    'INT',
    'float64':  'DOUBLE',
    'float32':  'FLOAT',
    'bool':     'TINYINT',
    'datetime64[ns]': 'DATETIME',
}

def get_db_engine():
    """Create and return SQLAlchemy engine for MariaDB ColumnStore connection"""
    host     = os.getenv('DB_HOST',     'mariadb')
    port     = os.getenv('DB_PORT',     '3306')
    user     = os.getenv('DB_USER',     'mlops_user')
    password = os.getenv('DB_PASSWORD', 'mlops_password')
    db_name  = os.getenv('DB_NAME',     'mlops_db')
    connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(connection_string)


def _build_create_sql(table_name: str, df: pd.DataFrame) -> str:
    """Build a CREATE TABLE statement using ColumnStore engine"""
    cols = []
    for col, dtype in df.dtypes.items():
        sql_type = _DTYPE_MAP.get(str(dtype), 'TEXT')
        cols.append(f"`{col}` {sql_type}")
    col_defs = ", ".join(cols)
    return f"CREATE TABLE IF NOT EXISTS `{table_name}` ({col_defs}) ENGINE=ColumnStore"


def write_to_db(df: pd.DataFrame, table_name: str, if_exists: str = 'replace', index: bool = False):
    """
    Write DataFrame to MariaDB ColumnStore table.

    Uses ENGINE=ColumnStore explicitly so the table is stored in columnar
    format, which is optimal for the OBT (One Big Table) analytical pattern.
    Falls back gracefully if ColumnStore plugin is unavailable.
    """
    engine = get_db_engine()

    with engine.begin() as conn:
        if if_exists == 'replace':
            conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))

        # Create table with ColumnStore engine
        create_sql = _build_create_sql(table_name, df)
        try:
            conn.execute(text(create_sql))
            print(f"🗄️  Table `{table_name}` created with ENGINE=ColumnStore")
        except Exception as e:
            # Graceful fallback: ColumnStore plugin not available (e.g. local dev)
            print(f"⚠️  ColumnStore unavailable ({e}), falling back to InnoDB.")
            fallback_sql = create_sql.replace("ENGINE=ColumnStore", "ENGINE=InnoDB")
            conn.execute(text(fallback_sql))

    # Insert data (table already exists, so use 'append')
    df.to_sql(table_name, con=engine, if_exists='append', index=index)
    print(f"✅ Loaded {len(df)} rows into `{table_name}`.")


def read_from_db(query: str) -> pd.DataFrame:
    """Read data from MariaDB ColumnStore into a DataFrame"""
    engine = get_db_engine()
    return pd.read_sql(query, con=engine)
