# tests/test_orchestrator.py

import pytest
from unittest.mock import Mock

from automation_app.orchestrator import AgenticOrchestrator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def classifier():
    classifier = Mock()
    classifier.classify.return_value = "intent:create_user"
    return classifier


@pytest.fixture
def planner():
    planner = Mock()
    planner.generate_plan.return_value = Mock(dict=Mock(return_value={"plan": "data"}))
    return planner


@pytest.fixture
def policy_engine():
    policy_engine = Mock()
    policy_engine.validate_plan.return_value = True
    return policy_engine


@pytest.fixture
def executor():
    executor = Mock()
    executor.run.return_value = True
    return executor


@pytest.fixture
def state_store():
    state_store = Mock()
    state_store.get_context.return_value = {"previous": "context"}
    return state_store


@pytest.fixture
def orchestrator(classifier, planner, policy_engine, executor, state_store):
    return AgenticOrchestrator(
        classifier=classifier,
        planner=planner,
        policy_engine=policy_engine,
        executor=executor,
        state_store=state_store,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_process_request_success(orchestrator, classifier, planner, policy_engine, executor, state_store):
    result = orchestrator.process_request(
        user_input="Create a new employee",
        session_id="session-123",
    )

    assert result == "Execution completed"

    classifier.classify.assert_called_once_with("Create a new employee")
    state_store.get_context.assert_called_once_with("session-123")
    planner.generate_plan.assert_called_once()
    policy_engine.validate_plan.assert_called_once()
    executor.run.assert_called_once()
    state_store.save_context.assert_called_once()


# ---------------------------------------------------------------------------
# Policy violation
# ---------------------------------------------------------------------------

def test_process_request_policy_violation(orchestrator, policy_engine, executor, state_store):
    policy_engine.validate_plan.return_value = False

    result = orchestrator.process_request(
        user_input="Delete all employees",
        session_id="session-456",
    )

    assert result == "Plan violates policy. Cannot execute."

    executor.run.assert_not_called()
    state_store.save_context.assert_not_called()


# ---------------------------------------------------------------------------
# Execution failure
# ---------------------------------------------------------------------------

def test_process_request_execution_failure(orchestrator, executor, state_store):
    executor.run.return_value = False

    result = orchestrator.process_request(
        user_input="Send email",
        session_id="session-789",
    )

    assert result == "Execution failed"

    executor.run.assert_called_once()
    state_store.save_context.assert_called_once()


# ---------------------------------------------------------------------------
# Parametrized execution outcomes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "executor_result, expected_message",
    [
        (True, "Execution completed"),
        (False, "Execution failed"),
    ],
    ids=["success", "failure"],
)
def test_process_request_execution_outcomes(
    orchestrator,
    executor,
    executor_result,
    expected_message,
):
    executor.run.return_value = executor_result

    result = orchestrator.process_request(
        user_input="Do something",
        session_id="session-999",
    )

    assert result == expected_message


# ---------------------------------------------------------------------------
# Persistence correctness
# ---------------------------------------------------------------------------

def test_state_is_persisted_with_last_plan(orchestrator, planner, state_store):
    plan = Mock()
    plan.dict.return_value = {"foo": "bar"}
    planner.generate_plan.return_value = plan

    orchestrator.process_request(
        user_input="Persist state",
        session_id="session-abc",
    )

    state_store.save_context.assert_called_once_with(
        "session-abc",
        {"last_plan": {"foo": "bar"}},
    )
