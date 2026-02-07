import asyncio
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from automation_app.models.action import Action
from automation_app.models.workflow_state import WorkflowState
from automation_app.models.plan import Plan
from automation_app.models.intent import Intent
from automation_app.orchestrator import AgenticOrchestrator


@pytest.fixture
def mock_components():
    return {
        "classifier": AsyncMock(),
        "planner": AsyncMock(),
        "policy_engine": AsyncMock(),
        "executor": AsyncMock(),
        "state_store": AsyncMock(),
        "auditor": MagicMock(),
    }


@pytest.fixture
def orchestrator(mock_components):
    return AgenticOrchestrator(**mock_components)


@pytest.fixture
def sample_intent():
    return Intent(
        name="test_intent",
        adapter="test_adapter",
        method="run",
        entities={"x": 1},
    )


@pytest.fixture
def sample_plan():
    return Plan(
        actions=[
            Action(
                adapter="TestAdapter",
                method="do_something",
                params={"a": 1},
            )
        ]
    )



# ---------------------------------------------------------
# PROCESS REQUEST (ASYNC BACKGROUND)
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_process_requestasync_executes_in_background(orchestrator, mock_components, sample_intent, sample_plan):
    mock_components["classifier"].classify.return_value = sample_intent
    mock_components["planner"].generate_plan.return_value = sample_plan
    mock_components["policy_engine"].validate_plan.return_value = True
    mock_components["state_store"].get_context.return_value = {}

    result = await orchestrator.process_requestasync("hello", "session1")

    assert result == "Execution started in background"
    mock_components["executor"].run.assert_not_awaited()  # background task, not awaited


@pytest.mark.asyncio
async def test_process_requestasync_policy_rejects(orchestrator, mock_components, sample_intent, sample_plan):
    mock_components["classifier"].classify.return_value = sample_intent
    mock_components["planner"].generate_plan.return_value = sample_plan
    mock_components["policy_engine"].validate_plan.return_value = False
    mock_components["state_store"].get_context.return_value = {}

    result = await orchestrator.process_requestasync("hello", "session1")

    assert result == "Plan violates policy. Cannot execute."
    mock_components["executor"].run.assert_not_called()


# ---------------------------------------------------------
# PROPOSE
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_propose_happy_path(orchestrator, mock_components, sample_intent, sample_plan):
    mock_components["classifier"].classify.return_value = sample_intent
    mock_components["planner"].generate_plan.return_value = sample_plan
    mock_components["policy_engine"].validate_plan.return_value = True
    mock_components["state_store"].get_context.return_value = {}

    result = await orchestrator.propose("hello", "session1")

    assert result["state"] == WorkflowState.PROPOSED
    assert "plan" in result
    mock_components["state_store"].save_context.assert_called_once()


@pytest.mark.asyncio
async def test_propose_policy_rejects(orchestrator, mock_components, sample_intent, sample_plan):
    mock_components["classifier"].classify.return_value = sample_intent
    mock_components["planner"].generate_plan.return_value = sample_plan
    mock_components["policy_engine"].validate_plan.return_value = False
    mock_components["state_store"].get_context.return_value = {}

    result = await orchestrator.propose("hello", "session1")

    assert result["state"] == WorkflowState.REJECTED
    assert result["plan"] is None
    mock_components["state_store"].save_context.assert_not_called()


# ---------------------------------------------------------
# CONFIRM
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_confirm_starts_execution(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": sample_plan.model_dump()},
    }

    result = await orchestrator.confirm("session1")

    assert result["state"] == WorkflowState.IN_PROGRESS
    mock_components["executor"].run.assert_not_awaited()
    mock_components["state_store"].save_context.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_no_proposal(orchestrator, mock_components):
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.REJECTED
    }

    result = await orchestrator.confirm("session1")

    assert result["message"] == "Nothing to confirm"
    mock_components["executor"].run.assert_not_called()


# ---------------------------------------------------------
# REJECT
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_reject_happy_path(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "data": {"last_plan": sample_plan.model_dump()},
    }

    result = await orchestrator.reject("session1")

    assert result["state"] == WorkflowState.REJECTED
    mock_components["state_store"].save_context.assert_called_once()


@pytest.mark.asyncio
async def test_reject_no_proposal(orchestrator, mock_components):
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.IN_PROGRESS
    }

    result = await orchestrator.reject("session1")

    assert result["message"] == "Nothing to reject"
    mock_components["state_store"].save_context.assert_not_called()


# ---------------------------------------------------------
# CLEANUP STALE PROPOSALS
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_cleanup_stale_proposals_rejects_atomic(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_all_sessions.return_value = ["session1"]
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "timestamp": 0,
        "data": {"last_plan": sample_plan.model_dump()},
    }

    # Ensure update_if_state_matches exists and returns True
    mock_components["state_store"].update_if_state_matches = AsyncMock(return_value=True)

    await orchestrator.cleanup_stale_proposals(timeout_seconds=1)

    mock_components["state_store"].update_if_state_matches.assert_awaited_once()
    mock_components["state_store"].save_context.assert_not_called()
    mock_components["auditor"].log.assert_called()


@pytest.mark.asyncio
async def test_cleanup_stale_proposals_skips_non_proposed(orchestrator, mock_components):
    mock_components["state_store"].get_all_sessions.return_value = ["session1"]
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.IN_PROGRESS
    }

    await orchestrator.cleanup_stale_proposals(timeout_seconds=1)

    mock_components["state_store"].save_context.assert_not_called()


# ---------------------------------------------------------
# EXECUTOR ERROR LOGGING
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_executor_error_is_logged(orchestrator, mock_components, sample_plan):
    mock_components["executor"].run.side_effect = Exception("boom")

    await orchestrator._run_with_audit(sample_plan, "session1")

    mock_components["auditor"].log.assert_called()


@pytest.mark.asyncio
async def test_user_context_merging(orchestrator):
    base = {
        "role": "Engineer",
        "department": "R&D",
        "user_context": {"timezone": "EST", "role": "SHOULD_NOT_OVERRIDE"},
    }

    result = orchestrator._build_user_context(base, "u1", None, None)

    assert result["role"] == "Engineer"
    assert result["department"] == "R&D"
    assert result["timezone"] == "EST"
    assert result["user_id"] == "u1"

def test_serialized_plan(orchestrator, sample_plan):
    result = orchestrator._get_serialized_plan(sample_plan)
    assert "actions" in result
    assert isinstance(result["actions"], list)

@pytest.mark.asyncio
async def test_run_with_audit_success(orchestrator, mock_components, sample_plan):
    mock_components["executor"].run.return_value = None

    await orchestrator._run_with_audit(sample_plan, "session1")

    mock_components["auditor"].log.assert_not_called()

@pytest.mark.asyncio
async def test_process_requestasync_context_merging(orchestrator, mock_components, sample_intent, sample_plan):
    mock_components["classifier"].classify.return_value = sample_intent
    mock_components["planner"].generate_plan.return_value = sample_plan
    mock_components["policy_engine"].validate_plan.return_value = True
    mock_components["state_store"].get_context.return_value = {
        "role": "Manager",
        "department": "Finance",
        "user_context": {"timezone": "CET"},
    }


    await orchestrator.process_requestasync("hello", "session1", user_id="u1")

    # Validate policy engine received merged context
    args, kwargs = mock_components["policy_engine"].validate_plan.call_args
    user_context = args[1]
    assert user_context["role"] == "Manager"
    assert user_context["department"] == "Finance"
    assert user_context["timezone"] == "CET"

@pytest.mark.asyncio
async def test_propose_uses_context_data(orchestrator, mock_components, sample_intent, sample_plan):
    mock_components["classifier"].classify.return_value = sample_intent
    mock_components["planner"].generate_plan.return_value = sample_plan
    mock_components["policy_engine"].validate_plan.return_value = True
    mock_components["state_store"].get_context.return_value = {
        "data": {"foo": "bar"}
    }

    await orchestrator.propose("hello", "session1")

    mock_components["planner"].generate_plan.assert_called_with(sample_intent, {"foo": "bar"})

@pytest.mark.asyncio
async def test_cleanup_stale_proposals_skips_fresh(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_all_sessions.return_value = ["session1"]
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "timestamp": time.time(),
        "data": {"last_plan": sample_plan.model_dump()},
    }

    await orchestrator.cleanup_stale_proposals(timeout_seconds=9999)

    mock_components["state_store"].save_context.assert_not_called()

@pytest.mark.asyncio
async def test_cleanup_stale_proposals_state_changes(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_all_sessions.return_value = ["session1"]

    # First call: stale
    mock_components["state_store"].get_context.side_effect = [
        {
            "state": WorkflowState.PROPOSED,
            "timestamp": 0,
            "data": {"last_plan": sample_plan.model_dump()},
        },
        # Second call: state changed before save
        {"state": WorkflowState.IN_PROGRESS}
    ]

    await orchestrator.cleanup_stale_proposals(timeout_seconds=1)

    mock_components["state_store"].save_context.assert_not_called()

@pytest.mark.asyncio
async def test_cleanup_stale_proposals_rejects_fallback(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_all_sessions.return_value = ["session1"]
    mock_components["state_store"].get_context.return_value = {
        "state": WorkflowState.PROPOSED,
        "timestamp": 0,
        "data": {"last_plan": sample_plan.model_dump()},
    }

    # Force fallback: no atomic method
    mock_components["state_store"].update_if_state_matches = None

    await orchestrator.cleanup_stale_proposals(timeout_seconds=1)

    mock_components["state_store"].save_context.assert_called_once()
    mock_components["auditor"].log.assert_called()

def test_get_serialized_plan_uses_model_dump_when_available(orchestrator, sample_plan):
    result = orchestrator._get_serialized_plan(sample_plan)
    assert "actions" in result
    assert isinstance(result["actions"], list)


def test_get_serialized_plan_falls_back_to_dict(orchestrator):
    class DummyPlan:
        def __init__(self):
            self.called = False

        def dict(self):
            self.called = True
            return {"foo": "bar"}

    dummy = DummyPlan()
    result = orchestrator._get_serialized_plan(dummy)

    assert result == {"foo": "bar"}
    assert dummy.called is True

@pytest.mark.asyncio
async def test_cleanup_stale_proposals_state_changes_fallback(orchestrator, mock_components, sample_plan):
    mock_components["state_store"].get_all_sessions.return_value = ["session1"]
    mock_components["state_store"].update_if_state_matches = None

    mock_components["state_store"].get_context.side_effect = [
        {
            "state": WorkflowState.PROPOSED,
            "timestamp": 0,
            "data": {"last_plan": sample_plan.model_dump()},
        },
        {"state": WorkflowState.IN_PROGRESS},
    ]

    await orchestrator.cleanup_stale_proposals(timeout_seconds=1)

    mock_components["state_store"].save_context.assert_not_called()
