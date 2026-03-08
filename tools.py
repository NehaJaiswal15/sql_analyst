# tools.py
import sqlite3
import pandas as pd
import os
import re

def load_csv_to_db(uploaded_file, custom_name: str = "") -> tuple[bool, str, str]:
    """
    Takes a Streamlit uploaded file + optional custom table name.
    Returns (success, table_name, message)
    """
    try:
        df = pd.read_csv(uploaded_file)

        # Clean column names
        df.columns = [
            re.sub(r'[^a-zA-Z0-9_]', '_', col.strip().lower())
            for col in df.columns
        ]

        # Use custom name if provided, else fall back to filename
        raw_name = custom_name.strip() if custom_name.strip() else uploaded_file.name.replace(".csv", "")
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', raw_name.lower())

        conn = sqlite3.connect("data/amazon.db")
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

        return True, table_name, f"✅ Loaded **{len(df)} rows** and **{len(df.columns)} columns** into table `{table_name}`"

    except Exception as e:
        return False, "", f"❌ Error loading CSV: {str(e)}"


def get_all_tables() -> list[str]:
    """Returns all table names currently in the DB"""
    conn = sqlite3.connect("data/amazon.db")
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'", conn
    )["name"].tolist()
    conn.close()
    return tables


def get_table_stats(table_name: str) -> dict:
    """Returns dynamic stats for any table"""
    conn = sqlite3.connect("data/amazon.db")
    stats = {}

    try:
        df = pd.read_sql(f"SELECT * FROM [{table_name}] LIMIT 1000", conn)
        stats["rows"]    = pd.read_sql(f"SELECT COUNT(*) as c FROM [{table_name}]", conn).iloc[0,0]
        stats["columns"] = len(df.columns)

        # Find numeric columns for avg stats
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        stats["numeric_cols"] = numeric_cols

        # Top 2 numeric columns for metrics
        stats["metrics"] = {}
        for col in numeric_cols[:2]:
            avg = pd.read_sql(f"SELECT ROUND(AVG([{col}]), 2) as a FROM [{table_name}]", conn).iloc[0,0]
            stats["metrics"][col] = avg

        stats["col_names"] = df.columns.tolist()

    except Exception as e:
        stats["error"] = str(e)

    conn.close()
    return stats