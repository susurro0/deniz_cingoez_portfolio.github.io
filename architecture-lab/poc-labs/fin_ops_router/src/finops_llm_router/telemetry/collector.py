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
        # Connect to DuckDB (file-based)
        self.conn = duckdb.connect(db_path)
        # Create table if it doesn't exist
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                timestamp TIMESTAMP,
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

    async def capture(
        self,
        request_id: str,
        strategy: str,
        provider: str,
        model: str,
        usage: Dict[str, int],
        cost_estimated: float,
        latency_ms: float,
    ) -> None:
        """
        Fire-and-forget async persistence to DuckDB, with console logging.
        """
        # Placeholder for async behavior
        await asyncio.sleep(0)

        self.conn.execute(
            """
            INSERT INTO telemetry 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow(),
                request_id,
                strategy,
                provider,
                model,
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
                cost_estimated,
                latency_ms,
            )
        )
        # Console/log visualization (Director-friendly)
        print(
            f"[Telemetry] {datetime.utcnow().isoformat()} | strategy={strategy} | "
            f"request_id={request_id} | provider={provider} | model={model} | "
            f"input_tokens={usage.get('input_tokens', 0)} | "
            f"output_tokens={usage.get('output_tokens', 0)} | "
            f"cost=${cost_estimated:.4f} | latency={latency_ms:.2f}ms"
        )

    def query_all(self):
        """
        Quick method to query all telemetry for debugging / dashboarding.
        """
        return self.conn.execute("SELECT * FROM telemetry").fetchall()
