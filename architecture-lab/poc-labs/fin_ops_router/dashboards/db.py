import duckdb

DB_PATH = "telemetry.duckdb"

def get_connection():
    """
    Returns a DuckDB connection to the telemetry database.
    """
    con = duckdb.connect(DB_PATH)
    return con

def fetch_telemetry(limit: int = 100):
    """
    Returns the latest telemetry entries.
    """
    con = get_connection()
    rows = con.execute(
        f"SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT {limit}"
    ).fetchall()
    return rows
