import pytest

from automation_app.utils.saga_step import SagaStep


# ---------------------------------------------------------------------------
# Base class behavior
# ---------------------------------------------------------------------------

def test_saga_step_cannot_be_instantiated():
    with pytest.raises(TypeError):
        SagaStep()  # abstract class cannot be instantiated

# ---------------------------------------------------------------------------
# Valid concrete implementation
# ---------------------------------------------------------------------------

class ValidStep(SagaStep):
    def execute(self, state):
        return f"executed:{state}"

    def compensate(self, state):
        return f"compensated:{state}"


def test_valid_step_instantiation():
    step = ValidStep()
    assert isinstance(step, SagaStep)


def test_valid_step_execute_and_compensate():
    step = ValidStep()

    assert step.execute("X") == "executed:X"
    assert step.compensate("X") == "compensated:X"


# ---------------------------------------------------------------------------
# Missing execute() should fail
# ---------------------------------------------------------------------------

class MissingExecute(SagaStep):
    def compensate(self, state):
        return "ok"


def test_missing_execute_raises_type_error():
    with pytest.raises(TypeError):
        MissingExecute()


# ---------------------------------------------------------------------------
# Missing compensate() should fail
# ---------------------------------------------------------------------------

class MissingCompensate(SagaStep):
    def execute(self, state):
        return "ok"


def test_missing_compensate_raises_type_error():
    with pytest.raises(TypeError):
        MissingCompensate()


# A subclass that calls super() so the abstract method body executes
class CallsSuper(SagaStep):
    def execute(self, state):
        return super().execute(state)

    def compensate(self, state):
        return super().compensate(state)


@pytest.mark.parametrize(
    "method, args",
    [
        ("execute", ("X",)),
        ("compensate", ("X",)),
    ],
    ids=["execute", "compensate"],
)
def test_abstract_methods_body_is_executed_and_returns_none(method, args):
    step = CallsSuper()

    # Calling the abstract method body should return None (because of pass)
    result = getattr(step, method)(*args)
    assert result is None