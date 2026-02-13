import asyncio
from typing import Dict


class TelemetryCollector:
    """
    Captures request and response telemetry asynchronously.
    This is the FinOps heartbeat of the platform.
    """

    async def capture(
        self,
        request_id: str,
        provider: str,
        model: str,
        usage: Dict[str, int],
        cost_estimated: float,
        latency_ms: float,
    ) -> None:
        # Fire-and-forget async persistence (DB / stream / queue later)
        await asyncio.sleep(0)  # placeholder for non-blocking write

        print(
            "[Telemetry]"
            f" request_id={request_id}"
            f" provider={provider}"
            f" model={model}"
            f" usage={usage}"
            f" cost=${cost_estimated:.4f}"
            f" latency_ms={latency_ms:.2f}"
        )
