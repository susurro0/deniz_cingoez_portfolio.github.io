import duckdb
import pandas as pd

DB_PATH = "telemetry.duckdb"

def init_db():
    """
    Ensures the table exists with the correct schema.
    """
    with duckdb.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                request_id VARCHAR,
                strategy VARCHAR,
                provider VARCHAR,
                model VARCHAR,
                usage_input INT,
                usage_output INT,
                cost_estimated DOUBLE,
                latency_ms DOUBLE
            )
        """)

def fetch_telemetry_df(limit: int = 100):
    """
    Returns the latest telemetry entries as a Pandas DataFrame.
    Using .df() is much faster for Streamlit than .fetchall().
    """
    # Use read_only=True to allow multiple Streamlit users to view simultaneously
    with duckdb.connect(DB_PATH, read_only=True) as con:
        df = con.execute(
            f"SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT {limit}"
        ).df()
    return df

def insert_telemetry(data_tuple):
    """
    Example helper to insert a new record.
    data_tuple: (request_id, strategy, provider, model, usage_input, usage_output, cost, latency)
    """
    with duckdb.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO telemetry 
            (request_id, strategy, provider, model, usage_input, usage_output, cost_estimated, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data_tuple)