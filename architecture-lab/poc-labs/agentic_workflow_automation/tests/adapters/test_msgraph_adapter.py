import pytest
from unittest.mock import patch, AsyncMock
from automation_app.adapters.msgraph_adapter import MSGraphAdapter

# ---------------------------------------------------------------------------
# execute()
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_execute_send_email_calls_send_email():
    adapter = MSGraphAdapter()

    with patch.object(adapter, "send_email", new_callable=AsyncMock, return_value={"message_id": "MSG-1"}) as mock_send:
        result = await adapter.execute("send_email", {"to": "a@example.com"})

        mock_send.assert_awaited_once_with({"to": "a@example.com"})
        assert result == {"message_id": "MSG-1"}

@pytest.mark.asyncio
async def test_execute_create_calendar_event_calls_method():
    adapter = MSGraphAdapter()

    with patch.object(adapter, "create_calendar_event", new_callable=AsyncMock, return_value={"event_id": "EVT-1"}) as mock_create:
        result = await adapter.execute("create_calendar_event", {"title": "Meeting"})

        mock_create.assert_awaited_once_with({"title": "Meeting"})
        assert result == {"event_id": "EVT-1"}

@pytest.mark.asyncio
async def test_execute_unsupported_action_raises():
    adapter = MSGraphAdapter()

    with pytest.raises(ValueError) as exc:
        await adapter.execute("unknown_action", {})

    assert "Unsupported MSGraph action" in str(exc.value)


# ---------------------------------------------------------------------------
# compensate()
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_compensate_send_email_calls_log_email_compensation():
    adapter = MSGraphAdapter()

    with patch.object(adapter, "log_email_compensation", new_callable=AsyncMock) as mock_log:
        await adapter.compensate("send_email", {"x": 1}, {"message_id": "MSG-1"})

        mock_log.assert_awaited_once_with({"message_id": "MSG-1"})

@pytest.mark.asyncio
async def test_compensate_calendar_event_calls_delete_calendar_event():
    adapter = MSGraphAdapter()

    with patch.object(adapter, "delete_calendar_event", new_callable=AsyncMock) as mock_delete:
        await adapter.compensate("create_calendar_event", {"x": 1}, {"event_id": "EVT-1"})

        mock_delete.assert_awaited_once_with("EVT-1")

@pytest.mark.asyncio
async def test_compensate_unknown_action_is_ignored():
    adapter = MSGraphAdapter()

    with patch.object(adapter, "delete_calendar_event", new_callable=AsyncMock) as mock_delete, \
         patch.object(adapter, "log_email_compensation", new_callable=AsyncMock) as mock_log:

        await adapter.compensate("weird_action", {}, {"id": 1})

        mock_delete.assert_not_awaited()
        mock_log.assert_not_awaited()


# ---------------------------------------------------------------------------
# supported_actions()
# ---------------------------------------------------------------------------
def test_supported_actions():
    adapter = MSGraphAdapter()
    assert adapter.supported_actions() == {"send_email", "create_calendar_event"}


# ---------------------------------------------------------------------------
# concrete methods
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_email_returns_message_id():
    adapter = MSGraphAdapter()
    result = await adapter.send_email({"to": "x@example.com"})
    assert result == {"message_id": "MSG-123"}

@pytest.mark.asyncio
async def test_create_calendar_event_returns_event_id():
    adapter = MSGraphAdapter()
    result = await adapter.create_calendar_event({"title": "Meeting"})
    assert result == {"event_id": "EVT-456"}

@pytest.mark.asyncio
async def test_delete_calendar_event_is_idempotent():
    adapter = MSGraphAdapter()

    # Should not raise
    await adapter.delete_calendar_event("EVT-1")

@pytest.mark.asyncio
async def test_log_email_compensation_is_noop():
    adapter = MSGraphAdapter()

    # Should not raise
    await adapter.log_email_compensation({"message_id": "MSG-1"})
