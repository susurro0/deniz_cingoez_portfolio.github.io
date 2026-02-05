import pytest
from unittest.mock import MagicMock, patch, ANY
from automation_app.models.workflow_state import WorkflowState
from automation_app.models.intent import Intent
from automation_app.orchestrator import AgenticOrchestrator


@pytest.fixture
def mocks():
    """Fixture to provide a collection of initialized mocks."""
    return {
        "classifier": MagicMock(),
        "planner": MagicMock(),
        "policy_engine": MagicMock(),
        "executor": MagicMock(),
        "state_store": MagicMock(),
        "auditor": MagicMock(),
        "scrubber": MagicMock()
    }


@pytest.fixture
def orchestrator(mocks):
    return AgenticOrchestrator(**mocks)


## --- Phase: process_request tests ---

@pytest.mark.parametrize("executor_success, expected_msg, expected_state", [
    (True, "Execution completed", WorkflowState.COMPLETED),
    (False, "Execution failed", WorkflowState.REJECTED),
])
def test_process_request_outcomes(orchestrator, mocks, executor_success, expected_msg, expected_state):
    # Setup
    mocks["scrubber"].scrub.return_value = "sanitized input"
    mocks["classifier"].classify.return_value = Intent(type="TEST", entity="X")

    mock_plan = MagicMock()
    mock_plan.model_dump.return_value = {"id": "plan_123"}
    mocks["planner"].generate_plan.return_value = mock_plan

    mocks["policy_engine"].validate_plan.return_value = True
    mocks["executor"].run.return_value = executor_success

    # Execute
    result = orchestrator.process_request("hello", "session-1")

    # Assert
    assert result == expected_msg
    mocks["state_store"].save_context.assert_called_with(
        "session-1", {"last_plan": {"id": "plan_123"}}, state=expected_state
    )


def test_process_request_policy_violation(orchestrator, mocks):
    mocks["policy_engine"].validate_plan.return_value = False

    result = orchestrator.process_request("bad input", "session-1")

    assert result == "Plan violates policy. Cannot execute."
    mocks["executor"].run.assert_not_called()


## --- Phase: propose tests ---

def test_propose_success(orchestrator, mocks):
    mocks["scrubber"].scrub.return_value = "sanitized"
    mocks["policy_engine"].validate_plan.return_value = True

    mock_plan = MagicMock()
    mock_plan.model_dump.return_value = {"id": "plan_abc"}
    mocks["planner"].generate_plan.return_value = mock_plan

    result = orchestrator.propose("do something", "sess-abc")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["plan"] == {"id": "plan_abc"}
    mocks["state_store"].save_context.assert_called_with(
        "sess-abc", {"last_plan": {"id": "plan_abc"}}, state=WorkflowState.PROPOSED
    )


def test_propose_policy_rejection(orchestrator, mocks):
    mocks["policy_engine"].validate_plan.return_value = False

    result = orchestrator.propose("do bad thing", "sess-abc")

    assert result["state"] == WorkflowState.REJECTED
    assert result["plan"] is None


## --- Phase: confirm & reject tests ---

def test_confirm_nothing_to_confirm(orchestrator, mocks):
    # State is not PROPOSED
    mocks["state_store"].get_context.return_value = {"state": WorkflowState.COMPLETED}

    result = orchestrator.confirm("sess-123")
    assert result["message"] == "Nothing to confirm"


@patch("automation_app.models.plan.Plan")  # Patch Plan to handle Plan(**plan_data)
def test_confirm_success(mock_plan_class, orchestrator, mocks):
    # Setup state store with a proposed plan
    plan_data = {"actions": []}
    mocks["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": plan_data}
    }
    mocks["executor"].run.return_value = True

    result = orchestrator.confirm("sess-123")

    assert result["state"] == WorkflowState.COMPLETED
    mocks["executor"].run.assert_called_once()
    mocks["state_store"].save_context.assert_called_with(
        "sess-123", {"last_plan": plan_data}, state=WorkflowState.COMPLETED
    )


def test_reject_success(orchestrator, mocks):
    plan_data = {"id": "123"}
    mocks["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": plan_data}
    }

    result = orchestrator.reject("sess-123")

    assert result["state"] == WorkflowState.REJECTED
    mocks["state_store"].save_context.assert_called_with(
        "sess-123", {"last_plan": plan_data}, state=WorkflowState.REJECTED
    )


def test_reject_invalid_state(orchestrator, mocks):
    mocks["state_store"].get_context.return_value = {"state": WorkflowState.COMPLETED}
    result = orchestrator.reject("sess-123")
    assert result["message"] == "Nothing to reject"


## --- Coverage for Compatibility Helpers ---

def test_get_serialized_plan_compatibility(orchestrator):
    # Test v1 (dict)
    v1_plan = MagicMock(spec=["dict"])
    v1_plan.dict.return_value = {"v": 1}
    assert orchestrator._get_serialized_plan(v1_plan) == {"v": 1}

    # Test v2 (model_dump)
    v2_plan = MagicMock(spec=["model_dump"])
    v2_plan.model_dump.return_value = {"v": 2}
    assert orchestrator._get_serialized_plan(v2_plan) == {"v": 2}