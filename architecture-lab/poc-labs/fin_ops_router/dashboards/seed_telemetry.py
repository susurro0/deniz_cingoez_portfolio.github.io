import duckdb
from datetime import datetime, timedelta
import random
import uuid

DB_PATH = "telemetry.duckdb"  # ensure it's in dashboards folder

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
    usage_input INTEGER,
    usage_output INTEGER,
    cost_estimated DOUBLE,
    latency_ms DOUBLE,
    guardrail_reason VARCHAR,
    guardrail_failed BOOLEAN,
    fallback_used BOOLEAN,
    provider_failed BOOLEAN,
)
""")

# Generate mock data
strategies = ["cost", "performance"]
providers = ["openai", "anthropic", "bedrock"]
models = ["GPT-4o-mini", "GPT-4", "Claude Haiku", "Claude 2", "Bedrock-X"]
forbidden_reasons = ["SSN detected", "Credit card detected"]

mock_rows = []

for i in range(100):
    ts = datetime.now() - timedelta(minutes=random.randint(0, 120))
    req_id = str(uuid.uuid4())

    # Randomly decide if this is a guardrail violation (10% chance)
    guardrail_failed = random.random() < 0.1
    if guardrail_failed:
        strategy = None
        provider = None
        model = None
        usage_input = None
        usage_output = None
        cost = None
        latency = None
        fallback = False
        provider_failed = False
        guardrail_reason = random.choice(forbidden_reasons)
    else:
        strategy = random.choice(strategies)
        provider = random.choice(providers)
        model = random.choice(models)
        usage_input = random.randint(50, 300)
        usage_output = random.randint(50, 300)
        cost = round(usage_input * 0.0001 + usage_output * 0.0001, 4)
        latency = round(random.uniform(50, 500), 2)
        fallback = random.random() < 0.2  # 20% chance
        provider_failed = random.random() < 0.05  # 5% chance
        guardrail_reason = None
        guardrail_failed = False

    mock_rows.append(
        (ts, req_id, strategy, provider, model, usage_input, usage_output, cost, latency,
         guardrail_reason, guardrail_failed, fallback, provider_failed )
    )

# Insert mock data
con.executemany(
    "INSERT INTO telemetry VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    mock_rows
)

print(f"Inserted {len(mock_rows)} mock telemetry rows into {DB_PATH}")
con.close()
