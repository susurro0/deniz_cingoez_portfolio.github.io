import pytest
from unittest.mock import MagicMock, patch, ANY

from automation_app.engines.execution_engine import ExecutionEngine
from automation_app.models.plan import Plan


# Assuming these are just Pydantic models or simple classes
class MockAction:
    def __init__(self, adapter, method, params):
        self.adapter = adapter
        self.method = method
        self.params = params


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    # Mock the supported_actions check
    adapter.supported_actions.return_value = ["create_user", "delete_user"]
    return adapter


@pytest.fixture
def engine(mock_adapter):
    adapters = {"identity_service": mock_adapter}
    # Mock auditor to avoid actual logging during tests
    return ExecutionEngine(adapters=adapters, state_store=MagicMock(), auditor=MagicMock())


## --- Success Path ---

def test_run_success(engine, mock_adapter):
    # Setup plan with one action
    action = MockAction("identity_service", "create_user", {"username": "test_user"})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]
    plan.dict.return_value = {"actions": []}

    result = engine.run(plan, session_id="123")

    assert result is True
    mock_adapter.execute.assert_called_once_with("create_user", {"username": "test_user"})
    engine.auditor.log.assert_any_call("123", "ACTION_SUCCEEDED", ANY)


## --- Failure & Rollback Path ---

def test_run_adapter_not_found_triggers_rollback(engine):
    action = MockAction("unknown_service", "do_thing", {})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # We spy on the rollback method
    with patch.object(engine, 'rollback') as mock_rollback:
        result = engine.run(plan, session_id="123")

        assert result is False
        mock_rollback.assert_called_once_with(plan, up_to_step=0, session_id="123")


def test_run_execution_exception_triggers_rollback(engine, mock_adapter):
    # Setup two actions; second one fails
    action1 = MockAction("identity_service", "create_user", {"id": 1})
    action2 = MockAction("identity_service", "create_user", {"id": 2})
    plan = MagicMock(spec=Plan)
    plan.actions = [action1, action2]
    plan.dict.return_value = {}

    # Force failure on the second call
    mock_adapter.execute.side_effect = [None, Exception("API Down")]

    result = engine.run(plan, session_id="456")

    assert result is False
    # Verify rollback was called for the failing step (index 1)
    # Rollback logic should try to compensate action 0
    assert mock_adapter.compensate.called
    mock_adapter.compensate.assert_called_with("create_user", {"id": 1})


## --- Logic Edge Cases ---

def test_unsupported_action_failure(engine, mock_adapter):
    # Method not in the supported_actions list
    action = MockAction("identity_service", "unsupported_method", {})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    result = engine.run(plan, session_id="789")

    assert result is False
    engine.auditor.log.assert_any_call("789", "EXECUTION_FAILED", ANY)


def test_rollback_handles_adapter_without_compensate(engine, mock_adapter):
    # Remove the compensate method to test hasattr check
    del mock_adapter.compensate

    action = MockAction("identity_service", "create_user", {})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # This should not raise an AttributeError
    engine.rollback(plan, up_to_step=1, session_id="123")


from unittest.mock import MagicMock, ANY


def test_rollback_compensation_failure_logging(engine, mock_adapter):
    """
    Tests the scenario where an action fails, and the subsequent
    attempt to roll back (compensate) also fails.
    """
    # 1. Setup a plan with one action
    action = MockAction("identity_service", "create_user", {"id": 1})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    # 2. Mock adapter: compensate() raises an Exception
    mock_adapter.compensate.side_effect = Exception("Database crash during rollback")

    # 3. Manually trigger rollback (or run a failing plan)
    # We call rollback directly to isolate the test to that specific catch block
    engine.rollback(plan, up_to_step=1, session_id="session_999")

    # 4. Assertions
    # Check if ACTION_COMPENSATION_FAILED was logged with the right context
    engine.auditor.log.assert_called_with(
        "session_999",
        "ACTION_COMPENSATION_FAILED",
        {
            "adapter": "identity_service",
            "method": "create_user",
            "step": 0,
            "error": "Database crash during rollback",
            "trace": ANY,
            "params": {"id": "1"}
        }
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