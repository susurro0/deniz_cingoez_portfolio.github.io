import pytest
from pydantic import ValidationError

from automation_app.models.orchestrator_response import OrchestratorResponse
from automation_app.models.workflow_state import WorkflowState


# ---------------------------------------------------------------------------
# Creation tests (parametrized)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "message, state, plan",
    [
        ("OK", None, None),
        ("Done", WorkflowState.COMPLETED, None),
        ("Proposed", WorkflowState.PROPOSED, {"foo": "bar"}),
        ("Rejected", WorkflowState.REJECTED, {"reason": "policy"}),
    ],
    ids=["minimal", "completed", "proposed_with_plan", "rejected_with_plan"],
)
def test_orchestrator_response_creation(message, state, plan):
    resp = OrchestratorResponse(message=message, state=state, plan=plan)

    assert resp.message == message
    assert resp.state == state
    assert resp.plan == plan


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

def test_orchestrator_response_missing_message():
    with pytest.raises(ValidationError):
        OrchestratorResponse()  # message is required


@pytest.mark.parametrize(
    "invalid_state",
    ["NOT_A_STATE", 123, 3.14, {"foo": "bar"}],
    ids=["string", "int", "float", "dict"],
)
def test_orchestrator_response_invalid_state(invalid_state):
    with pytest.raises(ValidationError):
        OrchestratorResponse(message="Hi", state=invalid_state)


# ---------------------------------------------------------------------------
# Serialization tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "state, plan",
    [
        (None, None),
        (WorkflowState.PROPOSED, {"x": 1}),
        (WorkflowState.COMPLETED, {"result": "ok"}),
    ],
    ids=["no_state_no_plan", "proposed_with_plan", "completed_with_plan"],
)
def test_orchestrator_response_serialization(state, plan):
    resp = OrchestratorResponse(
        message="Test",
        state=state,
        plan=plan,
    )

    dumped = resp.model_dump()

    assert dumped["message"] == "Test"
    assert dumped["state"] == state
    assert dumped["plan"] == plan


# ---------------------------------------------------------------------------
# Equality tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "a_kwargs, b_kwargs, expected_equal",
    [
        ({"message": "A"}, {"message": "A"}, True),
        ({"message": "A"}, {"message": "B"}, False),
        (
            {"message": "X", "state": WorkflowState.PROPOSED},
            {"message": "X", "state": WorkflowState.PROPOSED},
            True,
        ),
        (
            {"message": "X", "state": WorkflowState.PROPOSED},
            {"message": "X", "state": WorkflowState.COMPLETED},
            False,
        ),
    ],
    ids=["same_message", "different_message", "same_state", "different_state"],
)
def test_orchestrator_response_equality(a_kwargs, b_kwargs, expected_equal):
    a = OrchestratorResponse(**a_kwargs)
    b = OrchestratorResponse(**b_kwargs)

    assert (a == b) is expected_equal

