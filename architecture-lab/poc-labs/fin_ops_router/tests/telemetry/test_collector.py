import pytest
import asyncio
from finops_llm_router.telemetry.collector import TelemetryCollector


@pytest.fixture
def collector():
    # Use in-memory DuckDB for clean, isolated tests
    return TelemetryCollector(db_path=":memory:")


@pytest.mark.asyncio
async def test_capture_inserts_into_duckdb(collector):
    await collector.capture(
        request_id="req-123",
        provider="openai",
        model="gpt-4",
        usage={"input_tokens": 10, "output_tokens": 5},
        cost_estimated=0.003,
        latency_ms=12.34,
    )

    rows = collector.query_all()
    assert len(rows) == 1

    row = rows[0]

    # timestamp is row[0] → don't assert exact value
    assert row[1] == "req-123"
    assert row[2] == "openai"
    assert row[3] == "gpt-4"
    assert row[4] == 10
    assert row[5] == 5
    assert row[6] == 0.003
    assert row[7] == 12.34


@pytest.mark.asyncio
async def test_capture_awaits_sleep(monkeypatch, collector):
    sleep_called = False

    async def fake_sleep(duration):
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

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
async def test_capture_prints_expected_output(capsys, collector):
    await collector.capture(
        request_id="req-xyz",
        provider="anthropic",
        model="claude-3",
        usage={"input_tokens": 7, "output_tokens": 9},
        cost_estimated=0.0042,
        latency_ms=55.12,
    )

    out = capsys.readouterr().out.strip()

    # We cannot assert the timestamp, but we can assert the structure
    assert "[Telemetry]" in out
    assert "request_id=req-xyz" in out
    assert "provider=anthropic" in out
    assert "model=claude-3" in out
    assert "input_tokens=7" in out
    assert "output_tokens=9" in out
    assert "cost=$0.0042" in out
    assert "latency=55.12ms" in out


@pytest.mark.asyncio
async def test_query_all_returns_empty_initially(collector):
    assert collector.query_all() == []
