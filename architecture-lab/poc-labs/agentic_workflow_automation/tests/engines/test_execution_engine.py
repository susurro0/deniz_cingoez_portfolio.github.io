import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, ANY

from automation_app.engines.execution_engine import ExecutionEngine
from automation_app.models.action import Action
from automation_app.models.plan import Plan


class MockAction:
    def __init__(self, adapter, method, params):
        self.adapter = adapter
        self.method = method
        self.params = params


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()  # NOT AsyncMock
    adapter.supported_actions.return_value = ["send_email", "create_calendar_event"]

    adapter.execute_async = AsyncMock()
    adapter.compensate_async = AsyncMock()
    return adapter



@pytest.fixture
def engine(mock_adapter):
    adapters = {"identity_service": mock_adapter}
    return ExecutionEngine(adapters=adapters, state_store=MagicMock(), auditor=MagicMock())


## --- Success Paths ---

@pytest.mark.asyncio
async def test_run_success_async(engine, mock_adapter):
    # Setup
    action = MockAction("identity_service", "send_email", {"username": "test_user"})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]
    plan.dict.return_value = {"actions": []}

    result = await engine.run(plan, session_id="123")

    assert result is True
    mock_adapter.execute_async.assert_awaited_once_with("send_email", {"username": "test_user"})

    success_logs = [
        c for c in engine.auditor.log.call_args_list
        if c[0][1] == "ACTION_SUCCEEDED"
    ]

@pytest.mark.asyncio
async def test_run_success_sync_fallback(engine, mock_adapter):
    """Verifies engine falls back to .execute() if .execute_async() is missing."""
    action = MockAction("identity_service", "send_email", {"id": 1})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # Remove the async mock attribute to force fallback
    del mock_adapter.execute_async
    mock_adapter.execute = MagicMock()

    result = await engine.run(plan, session_id="123")

    assert result is True
    mock_adapter.execute.assert_called_once()


## --- Error & Rollback Paths ---

@pytest.mark.asyncio
async def test_run_unsupported_action_no_execution_no_rollback(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {"id": 1})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    result = await engine.run(plan, session_id="999")

    assert result is False
    mock_adapter.execute_async.assert_not_awaited()
    mock_adapter.compensate_async.assert_not_awaited()
    engine.auditor.log.assert_any_call("999", "EXECUTION_FAILED", ANY)


@pytest.mark.asyncio
async def test_rollback_compensation_failure_logging(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {"id": 1})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # Double failure: compensation fails too
    mock_adapter.compensate_async.side_effect = Exception("Critical Store Failure")

    await engine.rollback(plan, up_to_step=1, session_id="fail_999")

    engine.auditor.log.assert_called_with(
        "fail_999",
        "ACTION_COMPENSATION_FAILED",
        ANY
    )


def test_save_state_early_return(engine):
    """Verifies that if session_id is missing, save_context is never called."""
    plan = MagicMock(spec=Plan)

    # Reset engine to have no state_store for this test
    engine.state_store = None

    # This should not raise any errors or call any methods
    engine._save_state(None, plan, 0, "STARTED")

    # Ensure auditor wasn't even called for a failure
    engine.auditor.log.assert_not_called()


def test_save_state_exception_handling(engine):
    """Verifies that a failure in the state store is audited but doesn't crash."""
    plan = MagicMock(spec=Plan)
    plan.dict.return_value = {"actions": []}

    # Force the state store to fail
    engine.state_store.save_context.side_effect = Exception("Redis Connection Lost")

    # This should NOT raise an exception
    engine._save_state("session_123", plan, 0, "STARTED")

    # Verify the audit log captured the failure
    engine.auditor.log.assert_called_with(
        "session_123",
        "STATE_STORE_FAILURE",
        {"error": "Redis Connection Lost"}
    )


@pytest.mark.asyncio
async def test_run_adapter_missing(engine):
    # Action points to an adapter that doesn't exist in engine.adapters
    action = MockAction("missing_service", "do_thing", {})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    with patch.object(engine, 'rollback', new_callable=AsyncMock) as mock_rollback:
        result = await engine.run(plan, session_id="fail_1")

        assert result is False
        # Verify specific audit log
        engine.auditor.log.assert_any_call("fail_1", "ACTION_FAILED", ANY)
        # Verify rollback was called for step 0
        mock_rollback.assert_awaited_once_with(plan, up_to_step=0, session_id="fail_1")

@pytest.fixture
def make_plan():
    def _make(actions):
        return Plan(actions=actions)
    return _make


# ----------------------------------------------------------------------
# 1. Missing adapter → should rollback and return False
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_missing_adapter(engine, make_plan):
    engine.rollback = AsyncMock()
    plan = make_plan([
        Action(adapter="MissingAdapter", method="do", params={"x": 1})
    ])

    result = await engine.run(plan, session_id="s1")

    assert result is False
    engine.rollback.assert_awaited_once()
    engine.auditor.log.assert_any_call(
        "s1",
        "ACTION_FAILED",
        {
            "adapter": "MissingAdapter",
            "method": "do",
            "step": 0,
            "error": "No adapter found for MissingAdapter"
        }
    )


# ----------------------------------------------------------------------
# 2. Unsupported method → should rollback and return False
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_unsupported_method(engine, make_plan):
    # Create a fake adapter with no supported method
    fake_adapter = MagicMock()
    engine.rollback = AsyncMock()
    engine.adapters = {"Workday": fake_adapter}

    # Force _is_action_supported to return False
    engine._is_action_supported = MagicMock(return_value=False)

    plan = make_plan([
        Action(adapter="Workday", method="not_supported", params={"x": 1})
    ])

    result = await engine.run(plan, session_id="s2")

    assert result is False
    engine.rollback.assert_awaited_once()
    engine.auditor.log.assert_any_call(
        "s2",
        "EXECUTION_FAILED",
        {
            "adapter": "Workday",
            "method": "not_supported",
            "step": 0,
            "error": "Action 'not_supported' not supported by adapter 'Workday'"
        }
    )


# ----------------------------------------------------------------------
# 3. Adapter.execute raises exception → should rollback and return False
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_adapter_exception(engine, make_plan):
    class FakeAdapter:
        def execute(self, method, params):
            raise RuntimeError("boom")

    engine.rollback = AsyncMock()
    engine.adapters = {"Workday": FakeAdapter()}
    engine._is_action_supported = MagicMock(return_value=True)

    plan = make_plan([
        Action(adapter="Workday", method="create", params={"x": 1})
    ])

    result = await engine.run(plan, session_id="s3")

    assert result is False
    engine.rollback.assert_awaited_once()

    # ExecutionEngine logs ACTION_FAILED (no trace)
    failed_logs = [
        c for c in engine.auditor.log.call_args_list
        if c[0][1] == "ACTION_FAILED"
    ]
    assert len(failed_logs) == 1

    _, _, failed_payload = failed_logs[0][0]
    assert failed_payload["error"] == "boom"
    assert "trace" not in failed_payload

    # RecoveryEngine should NOT log ACTION_EXECUTION_ERROR for non-retry errors
    recovery_logs = [
        c for c in engine.auditor.log.call_args_list
        if c[0][1] == "ACTION_EXECUTION_ERROR"
    ]
    assert len(recovery_logs) == 0


@pytest.mark.asyncio
async def test_rollback_no_compensation_available(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # Remove all possible compensation methods from the mock
    del mock_adapter.compensate_async
    del mock_adapter.compensate

    # This should hit the 'continue' branch
    await engine.rollback(plan, up_to_step=1, session_id="roll_1")

    # Verify that NO compensation log was created
    for call in engine.auditor.log.call_args_list:
        assert call[0][1] != "ACTION_COMPENSATED"

@pytest.mark.asyncio
async def test_rollback_sync_fallback(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {"id": 5})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # Setup a synchronous compensation method
    del mock_adapter.compensate_async
    mock_adapter.compensate = MagicMock() # standard MagicMock is NOT a coroutine function

    await engine.rollback(plan, up_to_step=1, session_id="roll_sync")

    # Verify the sync method was called
    mock_adapter.compensate.assert_called_once_with("create_user", {"id": 5})
    # Verify the success log
    engine.auditor.log.assert_any_call("roll_sync", "ACTION_COMPENSATED", ANY)