import pytest
from pydantic import ValidationError

from automation_app.models.execution_failure import ExecutionFailure


def test_execution_failure_minimal_fields():
    failure = ExecutionFailure(
        adapter="Workday",
        method="create",
        step_idx=0,
        error_type="UNKNOWN",
        message="Something went wrong"
    )

    assert failure.adapter == "Workday"
    assert failure.method == "create"
    assert failure.step_idx == 0
    assert failure.error_type == "UNKNOWN"
    assert failure.message == "Something went wrong"
    assert failure.raw_error is None
    assert failure.context == {}  # default


def test_execution_failure_with_all_fields():
    failure = ExecutionFailure(
        adapter="Graph",
        method="send",
        step_idx=2,
        error_type="TRANSIENT",
        message="Timeout",
        raw_error="Traceback...",
        context={"retry": True, "attempt": 1}
    )

    assert failure.raw_error == "Traceback..."
    assert failure.context == {"retry": True, "attempt": 1}


def test_execution_failure_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        ExecutionFailure(
            adapter="X",
            method="y",
            # missing step_idx, error_type, message
        )


def test_execution_failure_rejects_wrong_types():
    with pytest.raises(ValidationError):
        ExecutionFailure(
            adapter=123,  # invalid
            method="go",
            step_idx="not-an-int",  # invalid
            error_type="UNKNOWN",
            message="bad types"
        )


def test_execution_failure_context_is_mutable_copy():
    # Ensure default {} is not shared across instances
    f1 = ExecutionFailure(
        adapter="A",
        method="m",
        step_idx=1,
        error_type="UNKNOWN",
        message="msg"
    )
    f2 = ExecutionFailure(
        adapter="A",
        method="m",
        step_idx=1,
        error_type="UNKNOWN",
        message="msg"
    )

    f1.context["x"] = 1

    assert f2.context == {}  # proves default is not shared
