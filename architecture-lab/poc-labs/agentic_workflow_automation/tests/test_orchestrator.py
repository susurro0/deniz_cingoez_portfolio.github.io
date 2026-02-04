import pytest
from unittest.mock import Mock, MagicMock, patch

from automation_app.orchestrator import AgenticOrchestrator
from automation_app.models.workflow_state import WorkflowState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def classifier():
    m = Mock()
    m.classify.return_value = "intent:create_user"
    return m


@pytest.fixture
def planner():
    m = Mock()
    m.generate_plan.return_value = Mock(dict=Mock(return_value={"plan": "data"}))
    return m


@pytest.fixture
def policy_engine():
    m = Mock()
    m.validate_plan.return_value = True
    return m


@pytest.fixture
def executor():
    m = Mock()
    m.run.return_value = True
    return m


@pytest.fixture
def state_store():
    m = Mock()
    m.get_context.return_value = {"data": {}, "state": WorkflowState.PROPOSED}
    return m


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
# process_request
# ---------------------------------------------------------------------------

def test_process_request_success(orchestrator, classifier, planner, policy_engine, executor, state_store):
    result = orchestrator.process_request("Create a new employee", "session-123")

    assert result == "Execution completed"
    classifier.classify.assert_called_once_with("Create a new employee")
    state_store.get_context.assert_called_once_with("session-123")
    planner.generate_plan.assert_called_once()
    policy_engine.validate_plan.assert_called_once()
    executor.run.assert_called_once()
    state_store.save_context.assert_called_once_with(
        "session-123",
        {"last_plan": {"plan": "data"}},
    )


def test_process_request_policy_violation(orchestrator, policy_engine, executor, state_store):
    policy_engine.validate_plan.return_value = False

    result = orchestrator.process_request("Delete all employees", "session-456")

    assert result == "Plan violates policy. Cannot execute."
    executor.run.assert_not_called()
    state_store.save_context.assert_not_called()


def test_process_request_execution_failure(orchestrator, executor, state_store):
    executor.run.return_value = False

    result = orchestrator.process_request("Send email", "session-789")

    assert result == "Execution failed"
    executor.run.assert_called_once()
    state_store.save_context.assert_called_once()


@pytest.mark.parametrize(
    "executor_result, expected",
    [(True, "Execution completed"), (False, "Execution failed")],
)
def test_process_request_parametrized(orchestrator, executor, executor_result, expected):
    executor.run.return_value = executor_result

    result = orchestrator.process_request("Do something", "session-999")

    assert result == expected


def test_process_request_persists_last_plan(orchestrator, planner, state_store):
    plan = Mock()
    plan.dict.return_value = {"foo": "bar"}
    planner.generate_plan.return_value = plan

    orchestrator.process_request("Persist state", "session-abc")

    state_store.save_context.assert_called_once_with(
        "session-abc",
        {"last_plan": {"foo": "bar"}},
    )


# ---------------------------------------------------------------------------
# propose
# ---------------------------------------------------------------------------

def test_propose_success(orchestrator, classifier, planner, policy_engine, state_store):
    planner.generate_plan.return_value = Mock(dict=lambda: {"plan": 1})
    policy_engine.validate_plan.return_value = True

    result = orchestrator.propose("hello", "session-1")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["message"] == "Plan proposed, awaiting confirmation"
    assert result["plan"] == {"plan": 1}

    state_store.save_context.assert_called_once_with(
        "session-1",
        {"last_plan": {"plan": 1}},
        state=WorkflowState.PROPOSED,
    )


def test_propose_rejected(orchestrator, policy_engine, state_store):
    policy_engine.validate_plan.return_value = False

    result = orchestrator.propose("hello", "session-1")

    assert result["state"] == WorkflowState.REJECTED
    assert result["message"] == "Plan violates policy"
    assert result["plan"] is None

    state_store.save_context.assert_not_called()


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------

def test_confirm_success(orchestrator, executor, state_store):
    state_store.get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": {"foo": "bar"}},
    }
    executor.run.return_value = True

    with patch("automation_app.orchestrator.Plan") as PlanMock:
        PlanMock.return_value = MagicMock()

        result = orchestrator.confirm("session-1")

        assert result["state"] == WorkflowState.COMPLETED
        assert result["message"] == "Execution completed"

        executor.run.assert_called_once()
        state_store.save_context.assert_called_once_with(
            "session-1",
            {"last_plan": {"foo": "bar"}},
            state=WorkflowState.COMPLETED,
        )


def test_confirm_wrong_state(orchestrator, state_store, executor):
    state_store.get_context.return_value = {
        "state": WorkflowState.EXECUTING,
        "data": {},
    }

    result = orchestrator.confirm("session-1")

    assert result["state"] == WorkflowState.EXECUTING
    assert result["message"] == "Nothing to confirm"

    executor.run.assert_not_called()
    state_store.save_context.assert_not_called()


def test_confirm_execution_failure(orchestrator, executor, state_store):
    state_store.get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": {"foo": "bar"}},
    }
    executor.run.return_value = False

    with patch("automation_app.orchestrator.Plan") as PlanMock:
        PlanMock.return_value = MagicMock()

        result = orchestrator.confirm("session-1")

        assert result["state"] == WorkflowState.REJECTED
        assert result["message"] == "Execution failed"

        state_store.save_context.assert_called_once_with(
            "session-1",
            {"last_plan": {"foo": "bar"}},
            state=WorkflowState.REJECTED,
        )

# ---------------------------------------------------------------------------
# reject
# ---------------------------------------------------------------------------

def test_reject_success(orchestrator, state_store):
    state_store.get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": {"foo": "bar"}}
    }

    result = orchestrator.reject("session-1")

    assert result["state"] == WorkflowState.REJECTED
    assert result["message"] == "Plan rejected by user"

    state_store.save_context.assert_called_once_with(
        "session-1",
        {"last_plan": {"foo": "bar"}},
        state=WorkflowState.REJECTED
    )


def test_reject_wrong_state(orchestrator, state_store):
    state_store.get_context.return_value = {
        "state": WorkflowState.EXECUTING,
        "data": {}
    }

    result = orchestrator.reject("session-1")

    assert result["state"] == WorkflowState.EXECUTING
    assert result["message"] == "Nothing to reject"

    state_store.save_context.assert_not_called()


def test_reject_preserves_last_plan(orchestrator, state_store):
    state_store.get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": {"x": 123}}
    }

    orchestrator.reject("session-abc")

    state_store.save_context.assert_called_once_with(
        "session-abc",
        {"last_plan": {"x": 123}},
        state=WorkflowState.REJECTED
    )
