import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from automation_app.models.workflow_state import WorkflowState
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan
from automation_app.orchestrator import AgenticOrchestrator


@pytest.fixture
def mocks():
    """Fixture to provide a collection of initialized mocks."""
    # Use AsyncMock for methods that are now awaited
    return {
        "classifier": AsyncMock(),
        "planner": AsyncMock(),
        "policy_engine": AsyncMock(),
        "executor": AsyncMock(),
        "state_store": AsyncMock(),
        "auditor": AsyncMock(),
        "scrubber": MagicMock()  # Still sync
    }


@pytest.fixture
def orchestrator(mocks):
    return AgenticOrchestrator(**mocks)

# Helper function for Intent
def make_intent(
    name="TEST",
    adapter="Workday",
    method="create_time_off",
    entities=None,
):
    return Intent(
        name=name,
        adapter=adapter,
        method=method,
        entities=entities or {},
    )
## --- Phase: process_request tests ---

@pytest.mark.asyncio
async def test_process_request_success(orchestrator, mocks):
    mocks["scrubber"].scrub.return_value = "sanitized input"
    mocks["classifier"].classify.return_value = make_intent()

    mock_plan = MagicMock(spec=Plan)
    mock_plan.model_dump.return_value = {"id": "plan_123"}
    mocks["planner"].generate_plan.return_value = mock_plan
    mocks["policy_engine"].validate_plan.return_value = True
    mocks["state_store"].get_context.return_value = {}

    result = await orchestrator.process_request("hello", "session-1")

    assert result == "Execution started in background"
    await asyncio.sleep(0)
    mocks["executor"].run.assert_called_once()



@pytest.mark.asyncio
async def test_process_request_policy_violation(orchestrator, mocks):
    mocks["policy_engine"].validate_plan.return_value = False
    mocks["classifier"].classify.return_value = make_intent()

    result = await orchestrator.process_request("bad input", "session-1")

    assert result == "Plan violates policy. Cannot execute."
    mocks["executor"].run.assert_not_called()


## --- Phase: propose tests ---

@pytest.mark.asyncio
async def test_propose_success(orchestrator, mocks):
    mocks["scrubber"].scrub.return_value = "sanitized"
    mocks["classifier"].classify.return_value = make_intent()
    mocks["policy_engine"].validate_plan.return_value = True
    mocks["state_store"].get_context.return_value = {}

    mock_plan = MagicMock(spec=Plan)
    mock_plan.model_dump.return_value = {"id": "plan_abc"}
    mocks["planner"].generate_plan.return_value = mock_plan

    result = await orchestrator.propose("do something", "sess-abc")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["plan"] == {"id": "plan_abc"}



## --- Phase: confirm & reject tests ---

@pytest.mark.asyncio
async def test_confirm_success(orchestrator, mocks):
    # Setup state store with a proposed plan
    plan_data = {"id": "plan_123"}
    mocks["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": plan_data}
    }

    # Patch Plan to avoid real Pydantic validation if needed,
    # but here we just need to ensure executor.run is triggered
    with patch("automation_app.orchestrator.Plan", return_value=MagicMock()):
        result = await orchestrator.confirm("sess-123")

    assert result["message"] == "Execution started in background"
    await asyncio.sleep(0)  # Yield control to background task
    mocks["executor"].run.assert_called_once()


@pytest.mark.asyncio
async def test_reject_success(orchestrator, mocks):
    plan_data = {"id": "123"}
    mocks["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": plan_data}
    }

    result = await orchestrator.reject("sess-123")

    assert result["state"] == WorkflowState.REJECTED
    mocks["state_store"].save_context.assert_called_with(
        "sess-123", {"last_plan": plan_data}, state=WorkflowState.REJECTED
    )


## --- Coverage for Compatibility Helpers (Remains Sync) ---

def test_get_serialized_plan_compatibility(orchestrator):
    v2_plan = MagicMock(spec=["model_dump"])
    v2_plan.model_dump.return_value = {"v": 2}
    assert orchestrator._get_serialized_plan(v2_plan) == {"v": 2}


## --- Missing Phase: process_request tests ---

@pytest.mark.asyncio
async def test_process_request_policy_violation(orchestrator, mocks):
    # Setup: Ensure internal calls return expected values
    mocks["scrubber"].scrub.return_value = "bad input"
    mocks["classifier"].classify.return_value = make_intent()
    mocks["state_store"].get_context.return_value = {}
    mocks["planner"].generate_plan.return_value = MagicMock(spec=Plan)

    # The trigger: Policy engine returns False
    mocks["policy_engine"].validate_plan.return_value = False

    result = await orchestrator.process_request("bad input", "session-1")

    assert result == "Plan violates policy. Cannot execute."
    # Verify execution was blocked
    mocks["executor"].run.assert_not_called()


## --- Missing Phase: confirm & reject tests ---

@pytest.mark.asyncio
async def test_reject_invalid_state(orchestrator, mocks):
    # Setup: State is already COMPLETED, so there is nothing to reject
    mocks["state_store"].get_context.return_value = {"state": WorkflowState.COMPLETED}

    result = await orchestrator.reject("sess-123")

    assert result["message"] == "Nothing to reject"
    assert result["state"] == WorkflowState.COMPLETED
    # Ensure we didn't accidentally save a REJECTED state
    mocks["state_store"].save_context.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.parametrize("is_valid, expected_msg", [
    (True, "Execution started in background"),
    (False, "Plan violates policy. Cannot execute."),
])
async def test_process_request_flow(orchestrator, mocks, is_valid, expected_msg):
    mocks["classifier"].classify.return_value = make_intent()
    mocks["state_store"].get_context.return_value = {}
    mocks["planner"].generate_plan.return_value = MagicMock(spec=Plan)
    mocks["policy_engine"].validate_plan.return_value = is_valid

    result = await orchestrator.process_request("hello", "session-1")

    assert result == expected_msg

@pytest.mark.asyncio
async def test_propose_policy_rejection_format(orchestrator, mocks):
    mocks["classifier"].classify.return_value = make_intent()
    mocks["planner"].generate_plan.return_value = MagicMock(spec=Plan)

    # Trigger rejection
    mocks["policy_engine"].validate_plan.return_value = False

    mocks["state_store"].get_context = AsyncMock(return_value={})

    result = await orchestrator.propose("bad intent", "sess-1")

    assert result == {
        "state": WorkflowState.REJECTED,
        "message": "Plan violates policy",
        "plan": None
    }



@pytest.mark.asyncio
async def test_confirm_invalid_state_guard(orchestrator, mocks):
    # Setup: Store is in 'COMPLETED' state, not 'PROPOSED'
    mocks["state_store"].get_context.return_value = {
        "state": WorkflowState.COMPLETED,
        "data": {}
    }

    result = await orchestrator.confirm("sess-1")

    assert result["state"] == WorkflowState.COMPLETED
    assert result["message"] == "Nothing to confirm"
    # Ensure executor was never triggered
    mocks["executor"].run.assert_not_called()

@pytest.mark.parametrize("plan_type", ["v1", "v2"])
def test_get_serialized_plan_compatibility(plan_type):
    orchestrator = AgenticOrchestrator()

    if plan_type == "v2":
        # Pydantic v2: plan has model_dump()
        plan = MagicMock(spec=["model_dump"])
        plan.model_dump.return_value = {"version": "v2"}
        result = orchestrator._get_serialized_plan(plan)
        assert result == {"version": "v2"}
        plan.model_dump.assert_called_once()

    else:
        # Pydantic v1: plan has dict()
        plan = MagicMock(spec=["dict"])
        plan.dict.return_value = {"version": "v1"}
        result = orchestrator._get_serialized_plan(plan)
        assert result == {"version": "v1"}
        plan.dict.assert_called_once()
