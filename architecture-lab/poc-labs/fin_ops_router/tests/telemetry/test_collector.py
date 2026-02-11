import pytest
import asyncio

from finops_llm_router.telemetry.collector import TelemetryCollector


@pytest.mark.asyncio
async def test_capture_prints_expected_output(capsys):
    collector = TelemetryCollector()

    await collector.capture(
        prompt="hello",
        response="world",
        model_used="gpt-4"
    )

    captured = capsys.readouterr().out.strip()
    assert captured == "[Telemetry] model=gpt-4, prompt='hello', response='world'"


@pytest.mark.asyncio
async def test_capture_awaits_sleep(monkeypatch):
    sleep_called = False

    async def fake_sleep(duration):
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    collector = TelemetryCollector()
    await collector.capture("p", "r", "m")

    assert sleep_called is True


@pytest.mark.asyncio
async def test_capture_does_not_raise():
    collector = TelemetryCollector()

    # Should run without throwing exceptions
    await collector.capture("prompt", "response", "model")
