import pytest
from unittest.mock import patch, AsyncMock

from automation_app.adapters.workday_adapter import WorkdayAdapter


# ---------------------------------------------------------------------------
# execute()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_create_time_off_calls_method():
    adapter = WorkdayAdapter()

    with patch.object(adapter, "create_time_off", new_callable=AsyncMock, return_value={"request_id": "WD999"}) as mock_create:
        result = await adapter.execute("create_time_off", {"days": 1})

        mock_create.assert_awaited_once_with({"days": 1})
        assert result == {"request_id": "WD999"}


@pytest.mark.asyncio
async def test_execute_unsupported_action_raises():
    adapter = WorkdayAdapter()

    with pytest.raises(ValueError) as exc:
        await adapter.execute("unknown_action", {})

    assert "Unsupported action" in str(exc.value)


# ---------------------------------------------------------------------------
# compensate()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compensate_calls_cancel_time_off_when_request_id_present():
    adapter = WorkdayAdapter()

    with patch.object(adapter, "cancel_time_off") as mock_cancel:
        await adapter.compensate("create_time_off", {"days": 1}, {"request_id": "WD123"})

        mock_cancel.assert_called_once_with("WD123")


@pytest.mark.asyncio
async def test_compensate_does_nothing_when_request_id_missing():
    adapter = WorkdayAdapter()

    with patch.object(adapter, "cancel_time_off") as mock_cancel:
        await adapter.compensate("create_time_off", {"days": 1}, {})

        mock_cancel.assert_not_called()


@pytest.mark.asyncio
async def test_compensate_ignores_unknown_action():
    adapter = WorkdayAdapter()

    with patch.object(adapter, "cancel_time_off") as mock_cancel:
        await adapter.compensate("weird_action", {}, {"request_id": "WD123"})

        mock_cancel.assert_not_called()


# ---------------------------------------------------------------------------
# supported_actions()
# ---------------------------------------------------------------------------

def test_supported_actions():
    adapter = WorkdayAdapter()
    assert adapter.supported_actions() == {"create_time_off"}


# ---------------------------------------------------------------------------
# concrete methods
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_time_off_returns_request_id():
    adapter = WorkdayAdapter()
    result = await adapter.create_time_off({"days": 2})

    assert result == {"request_id": "WD123"}


@pytest.mark.asyncio
async def test_cancel_time_off_is_idempotent():
    adapter = WorkdayAdapter()

    # Should not raise
    await adapter.cancel_time_off("WD123")
