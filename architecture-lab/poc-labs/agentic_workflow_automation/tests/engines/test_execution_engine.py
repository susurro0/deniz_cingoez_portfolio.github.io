import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, ANY

from automation_app.config.constants import RecoveryDecision
from automation_app.engines.exceptions import ActionFailure
from automation_app.engines.execution_engine import ExecutionEngine
from automation_app.models.action import Action
from automation_app.models.plan import Plan
from automation_app.models.workflow_state import WorkflowState


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

    mock_planner = AsyncMock()

    return ExecutionEngine(
        adapters=adapters,
        state_store=MagicMock(),
        auditor=MagicMock(),
        planner=mock_planner
    )
## --- Success Paths ---

@pytest.mark.asyncio
async def test_run_success_async(engine, mock_adapter):
    action = Action(adapter="identity_service", method="send_email", params={"username": "test_user"})
    plan = Plan(actions=[action])

    result = await engine.run(plan, session_id="123")

    assert result is True
    mock_adapter.execute_async.assert_awaited_once_with("send_email", {"username": "test_user"})

    engine.auditor.log.assert_any_call(
        "123",
        WorkflowState.PROPOSED,
        {"adapter": "identity_service", "method": "send_email", "step": 0},
    )


@pytest.mark.asyncio
async def test_run_success_sync_fallback(engine, mock_adapter):
    action = Action(adapter="identity_service", method="send_email", params={"id": 1})
    plan = Plan(actions=[action])

    del mock_adapter.execute_async
    mock_adapter.execute = MagicMock()

    result = await engine.run(plan, session_id="123")

    assert result is True
    mock_adapter.execute.assert_called_once_with("send_email", {"id": 1})


## --- Error & Rollback Paths ---

@pytest.mark.asyncio
async def test_run_unsupported_action(engine, mock_adapter):
    action = Action(adapter="identity_service", method="create_user", params={"id": 1})
    plan = Plan(actions=[action])

    engine._is_action_supported = MagicMock(return_value=False)
    engine.rollback = AsyncMock()

    result = await engine.run(plan, session_id="999")

    assert result is False
    engine.rollback.assert_awaited_once()

    engine.auditor.log.assert_any_call(
        "999",
        "ACTION_FAILED",
        {
            "adapter": "identity_service",
            "method": "create_user",
            "step": 0,
            "error": "Action 'create_user' not supported by adapter 'identity_service'",
        },
    )

@pytest.mark.asyncio
async def test_rollback_compensation_failure_logging(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {"id": 1})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

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
async def test_run_missing_adapter():
    engine = ExecutionEngine(adapters={})
    engine.scrubber = MagicMock()
    engine.scrubber.scrub_data.return_value = {"x": 1}
    engine._audit = MagicMock()
    engine._save_state = MagicMock()
    engine.rollback = AsyncMock()

    plan = Plan(actions=[
        Action(adapter="Missing", method="do", params={"x": 1})
    ])

    result = await engine.run(plan, session_id="S1")

    assert result is False
    engine.rollback.assert_awaited_once()

    engine._audit.assert_any_call(
        "S1",
        "ACTION_FAILED",
        {
            "adapter": "Missing",
            "method": "do",
            "step": 0,
            "error": "No adapter found for Missing",
        },
    )


# ----------------------------------------------------------------------
# 2. Unsupported method → should rollback and return False
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_unsupported_method():
    fake_adapter = MagicMock()
    engine = ExecutionEngine(adapters={"Workday": fake_adapter})
    engine.scrubber = MagicMock()
    engine.scrubber.scrub_data.return_value = {"x": 1}
    engine._audit = MagicMock()
    engine._save_state = MagicMock()
    engine.rollback = AsyncMock()

    engine._is_action_supported = MagicMock(return_value=False)

    plan = Plan(actions=[
        Action(adapter="Workday", method="not_supported", params={"x": 1})
    ])

    result = await engine.run(plan, session_id="S2")

    assert result is False
    engine.rollback.assert_awaited_once()

    engine._audit.assert_any_call(
        "S2",
        "ACTION_FAILED",
        {
            "adapter": "Workday",
            "method": "not_supported",
            "step": 0,
            "error": "Action 'not_supported' not supported by adapter 'Workday'",
        },
    )


# ----------------------------------------------------------------------
# 3. Adapter.execute raises exception → should rollback and return False
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_adapter_exception_triggers_replan(engine):
    class FakeAdapter:
        def execute(self, method, params):
            raise RuntimeError("boom")

    engine.adapters = {"Workday": FakeAdapter()}
    engine._is_action_supported = MagicMock(return_value=True)

    engine.recovery.attempt_with_recovery = AsyncMock(
        side_effect=ActionFailure(
            decision=RecoveryDecision.FAIL,
            original=RuntimeError("boom")
        )
    )

    engine.rollback = AsyncMock()
    engine._replan_on_failure = AsyncMock(return_value=False)

    plan = Plan(actions=[Action(adapter="Workday", method="create", params={"x": 1})])

    result = await engine.run(plan, session_id="s3")

    assert result is False
    engine.rollback.assert_awaited_once()
    engine._replan_on_failure.assert_awaited_once()

@pytest.mark.asyncio
async def test_run_adapter_exception_triggers_re_plan(engine):
    class FakeAdapter:
        def execute(self, method, params):
            raise RuntimeError("boom")

    engine.adapters = {"Workday": FakeAdapter()}
    engine._is_action_supported = MagicMock(return_value=True)

    engine.recovery.attempt_with_recovery = AsyncMock(
        side_effect=ActionFailure(
            decision=RecoveryDecision.FAIL,
            original=RuntimeError("boom")
        )
    )

    engine.rollback = AsyncMock()
    engine._replan_on_failure = AsyncMock(return_value=False)

    plan = Plan(actions=[Action(adapter="Workday", method="create", params={"x": 1})])

    result = await engine.run(plan, session_id="s3")

    assert result is False
    engine.rollback.assert_awaited_once()
    engine._replan_on_failure.assert_awaited_once()


@pytest.mark.asyncio
async def test_rollback_no_compensation_available(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    del mock_adapter.compensate_async
    del mock_adapter.compensate

    await engine.rollback(plan, up_to_step=1, session_id="roll_1")

    for call in engine.auditor.log.call_args_list:
        assert call[0][1] != "ACTION_COMPENSATED"

@pytest.mark.asyncio
async def test_rollback_sync_fallback(engine, mock_adapter):
    action = MockAction("identity_service", "create_user", {"id": 5})
    plan = MagicMock(spec=Plan)
    plan.actions = [action]

    del mock_adapter.compensate_async
    mock_adapter.compensate = MagicMock() # standard MagicMock is NOT a coroutine function

    await engine.rollback(plan, up_to_step=1, session_id="roll_sync")

    mock_adapter.compensate.assert_called_once_with("create_user", {"id": 5})
    engine.auditor.log.assert_any_call("roll_sync", "ACTION_COMPENSATED", ANY)


@pytest.mark.asyncio
async def test_replan_on_failure_triggers_audit_and_returns_false():
    engine = ExecutionEngine(adapters={})

    # Give engine a planner mock with repair_plan
    mock_planner = MagicMock()
    mock_planner.repair_plan = AsyncMock(return_value=None)
    engine.planner = mock_planner

    # Patch audit
    engine._audit = MagicMock()

    plan = Plan(actions=[
        Action(adapter="Workday", method="create_time_off", params={"x": 1})
    ])

    failed_action = plan.actions[0]

    result = await engine._replan_on_failure(
        plan=plan,
        failed_action=failed_action,
        decision=RecoveryDecision.FAIL,
        session_id="session_42",
    )

    # Validate return value
    assert result is False

    # Validate audit log
    engine._audit.assert_called_once_with(
        "session_42",
        "REPLAN_TRIGGERED",
        {
            "adapter": "Workday",
            "method": "create_time_off",
            "decision": "FAIL",
        },
    )
@pytest.mark.asyncio
async def test_execute_action_with_recovery_unexpected_exception():
    # Fake adapter with no async method
    class FakeAdapter:
        def execute(self, method, params):
            return None

    # Engine with mocked recovery engine
    engine = ExecutionEngine(adapters={"Workday": FakeAdapter()})
    engine._audit = MagicMock()

    # Force recovery engine to throw a non-ActionFailure exception
    engine.recovery.attempt_with_recovery = AsyncMock(
        side_effect=ValueError("unexpected boom")
    )

    action = Action(
        adapter="Workday",
        method="create_time_off",
        params={"x": 1},
    )

    # The method should re-raise the ValueError
    with pytest.raises(ValueError):
        await engine._execute_action_with_recovery(
            action=action,
            adapter=FakeAdapter(),
            session_id="S4",
            step_idx=0,
        )

    # Verify audit log was written correctly
    engine._audit.assert_called_once_with(
        "S4",
        "ACTION_FAILED",
        {
            "adapter": "Workday",
            "method": "create_time_off",
            "step": 0,
            "error": "unexpected boom",
        },
    )

@pytest.mark.asyncio
async def test_replan_on_failure_with_repaired_plan_reruns():
    # --- Setup ---
    # Create a fake plan and a failing action
    failed_action = Action(adapter="Workday", method="create_time_off", params={"x": 1})
    original_plan = Plan(actions=[failed_action])

    # Create a repaired plan to be returned by the planner
    repaired_action = Action(adapter="Workday", method="approve_time_off", params={"x": 1})
    repaired_plan = Plan(actions=[repaired_action])

    # Create ExecutionEngine with mocked planner, auditor, and run
    engine = ExecutionEngine(adapters={})
    engine._audit = MagicMock()
    engine.auditor = MagicMock()
    engine.planner = AsyncMock()
    engine.planner.repair_plan = AsyncMock(return_value=repaired_plan)
    engine.run = AsyncMock(return_value=True)  # pretend rerun succeeds

    # --- Exercise ---
    result = await engine._replan_on_failure(
        plan=original_plan,
        failed_action=failed_action,
        decision=RecoveryDecision.FAIL,
        session_id="session_42",
    )

    # --- Verify ---
    # The return value should be whatever `run` returned
    assert result is True

    # `_audit` should be called for REPLAN_TRIGGERED
    engine._audit.assert_called_with(
        "session_42",
        "REPLAN_TRIGGERED",
        {
            "adapter": "Workday",
            "method": "create_time_off",
            "decision": "FAIL",  # because decision.value is logged
        },
    )

    # Planner.repair_plan should have been called once
    engine.planner.repair_plan.assert_awaited_once_with(
        failed_plan=original_plan,
        failed_action=failed_action,
        decision=RecoveryDecision.FAIL,
    )

    # run() should have been called with the repaired plan
    engine.run.assert_awaited_once_with(repaired_plan, session_id="session_42")

    # Auditor.log should log PLAN_REPAIRED
    engine.auditor.log.assert_any_call(
        "session_42",
        "PLAN_REPAIRED",
        {
            "original_action": "create_time_off",
            "new_plan": ["approve_time_off"],
        },
    )
