import asyncio
from typing import Dict
import duckdb
from datetime import datetime

class TelemetryCollector:
    """
    Captures request and response telemetry asynchronously.
    This is the FinOps heartbeat of the platform.
    """

    def __init__(self, db_path: str = "telemetry.duckdb"):
        self.conn = duckdb.connect(db_path)
        # Create table if not exists
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                timestamp TIMESTAMP,
                request_id VARCHAR,
                provider VARCHAR,
                model VARCHAR,
                usage_input INT,
                usage_output INT,
                cost_estimated DOUBLE,
                latency_ms DOUBLE
            )
        """)

    async def capture(
        self,
        request_id: str,
        provider: str,
        model: str,
        usage: Dict[str, int],
        cost_estimated: float,
        latency_ms: float,
    ) -> None:
        # Fire-and-forget async persistence
        await asyncio.sleep(0)  # placeholder for non-blocking write

        # Insert into DuckDB
        self.conn.execute(
            """
            INSERT INTO telemetry
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow(),
                request_id,
                provider,
                model,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                cost_estimated,
                latency_ms,
            )
        )

        print(
            "[Telemetry]"
            f" request_id={request_id}"
            f" provider={provider}"
            f" model={model}"
            f" usage={usage}"
            f" cost=${cost_estimated:.4f}"
            f" latency_ms={latency_ms:.2f}"
        )
