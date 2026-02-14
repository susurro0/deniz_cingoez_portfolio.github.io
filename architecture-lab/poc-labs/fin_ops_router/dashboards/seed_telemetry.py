import duckdb
from datetime import datetime, timedelta
import random
import uuid

DB_PATH = "telemetry.duckdb"

# Connect to DuckDB (creates file if not exists)
con = duckdb.connect(DB_PATH)

# Create telemetry table if it doesn't exist
con.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    timestamp TIMESTAMP,
    request_id VARCHAR,
    strategy VARCHAR,
    provider VARCHAR,
    model VARCHAR,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_estimated DOUBLE,
    latency_ms DOUBLE
)
""")

# Generate mock data
strategies = ["cost-first", "performance-first"]
providers = ["openai", "anthropic", "bedrock"]
models = ["GPT-4o-mini", "GPT-4", "Claude Haiku", "Claude 2", "Bedrock-X"]

mock_rows = []

for i in range(100):
    ts = datetime.now() - timedelta(minutes=random.randint(0, 120))
    req_id = str(uuid.uuid4())
    strat = random.choice(strategies)
    prov = random.choice(providers)
    model = random.choice(models)
    input_tokens = random.randint(50, 300)
    output_tokens = random.randint(50, 300)
    cost = round(input_tokens * 0.0001 + output_tokens * 0.0001, 4)
    latency = round(random.uniform(50, 500), 2)

    mock_rows.append((ts, req_id, strat, prov, model, input_tokens, output_tokens, cost, latency))

# Insert mock data
con.executemany(
    "INSERT INTO telemetry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    mock_rows
)

print(f"Inserted {len(mock_rows)} mock telemetry rows into {DB_PATH}")
con.close()
