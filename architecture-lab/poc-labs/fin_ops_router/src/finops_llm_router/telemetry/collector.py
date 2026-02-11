import asyncio

class TelemetryCollector:
    """
    Captures request and response telemetry asynchronously.
    """

    async def capture(self, prompt: str, response: str, model_used: str):
        await asyncio.sleep(0)  # Placeholder for async DB write
        print(f"[Telemetry] model={model_used}, prompt='{prompt}', response='{response}'")
