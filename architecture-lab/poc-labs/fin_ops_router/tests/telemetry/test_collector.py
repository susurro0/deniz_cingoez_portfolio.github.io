import pytest
import asyncio
from finops_llm_router.telemetry.collector import TelemetryCollector


@pytest.mark.asyncio
async def test_capture_prints_expected_output(capsys):
    collector = TelemetryCollector()

    await collector.capture(
        request_id="req-123",
        provider="openai",
        model="gpt-4",
        usage={"input_tokens": 10, "output_tokens": 5},
        cost_estimated=0.003,
        latency_ms=12.34,
    )

    captured = capsys.readouterr().out.strip()

    assert captured == (
        "[Telemetry]"
        " request_id=req-123"
        " provider=openai"
        " model=gpt-4"
        " usage={'input_tokens': 10, 'output_tokens': 5}"
        " cost=$0.0030"
        " latency_ms=12.34"
    )


@pytest.mark.asyncio
async def test_capture_awaits_sleep(monkeypatch):
    sleep_called = False

    async def fake_sleep(duration):
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    collector = TelemetryCollector()

    await collector.capture(
        request_id="req-1",
        provider="openai",
        model="gpt-4",
        usage={"input_tokens": 1, "output_tokens": 1},
        cost_estimated=0.001,
        latency_ms=1.0,
    )

    assert sleep_called is True


@pytest.mark.asyncio
async def test_capture_does_not_raise():
    collector = TelemetryCollector()

    await collector.capture(
        request_id="abc",
        provider="openai",
        model="gpt-4",
        usage={"input_tokens": 1, "output_tokens": 1},
        cost_estimated=0.001,
        latency_ms=5.0,
    )
