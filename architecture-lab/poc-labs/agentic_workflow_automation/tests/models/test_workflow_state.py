# tests/models/test_workflow_state.py

import pytest
from automation_app.models.workflow_state import WorkflowState


def test_workflow_state_members_exist():
    assert WorkflowState.PROPOSED.value == "PROPOSED"
    assert WorkflowState.CONFIRMED.value == "CONFIRMED"
    assert WorkflowState.EXECUTING.value == "EXECUTING"
    assert WorkflowState.COMPLETED.value == "COMPLETED"
    assert WorkflowState.REJECTED.value == "REJECTED"
    assert WorkflowState.IN_PROGRESS.value == "IN PROGRESS"


def test_workflow_state_iteration():
    states = list(WorkflowState)
    assert len(states) == 6
    assert WorkflowState.PROPOSED in states
    assert WorkflowState.REJECTED in states


@pytest.mark.parametrize(
    "state_str, expected_enum",
    [
        ("PROPOSED", WorkflowState.PROPOSED),
        ("CONFIRMED", WorkflowState.CONFIRMED),
        ("EXECUTING", WorkflowState.EXECUTING),
        ("COMPLETED", WorkflowState.COMPLETED),
        ("REJECTED", WorkflowState.REJECTED),
    ],
)
def test_workflow_state_from_string(state_str, expected_enum):
    assert WorkflowState(state_str) == expected_enum


def test_workflow_state_invalid_value():
    with pytest.raises(ValueError):
        WorkflowState("NOT_A_STATE")
