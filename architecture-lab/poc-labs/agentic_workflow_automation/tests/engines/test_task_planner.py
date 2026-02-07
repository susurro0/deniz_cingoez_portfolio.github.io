import pytest
from types import SimpleNamespace

from automation_app.config.constants import RecoveryDecision
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan
from automation_app.models.action import Action
from automation_app.engines.task_planner import TaskPlanner


@pytest.fixture
def sample_plan():
    return Plan(actions=[
        Action(adapter="Workday", method="create_time_off", params={"x": 1}),
        Action(adapter="MSGraph", method="create_calendar_event", params={"y": 2})
    ])

@pytest.mark.asyncio
async def test_generate_plan_pto_intent():
    planner = TaskPlanner()

    intent = Intent(
        name="REQUEST_TIME_OFF",
        adapter="Workday",
        method="create_time_off",
        entities={"date": "Friday"}
    )

    state = {"user_id": "user123"}

    plan: Plan = await planner.generate_plan(intent, state)

    # Ensure Plan object
    assert isinstance(plan, Plan)
    assert len(plan.actions) == 2

    # First action: MSGraph create_calendar_event
    first_action = plan.actions[0]
    assert isinstance(first_action, Action)
    assert first_action.adapter == "MSGraph"
    assert first_action.method == "create_calendar_event"
    assert first_action.params["date"] == "Friday"
    assert first_action.params["user_id"] == "user123"

    # Second action: Workday create_time_off
    second_action = plan.actions[1]
    assert isinstance(second_action, Action)
    assert second_action.adapter == "Workday"
    assert second_action.method == "create_time_off"
    assert second_action.params["dates"] == ["Friday"]
    assert second_action.params["user_id"] == "user123"


@pytest.mark.asyncio
async def test_generate_plan_unsupported_intent_raises():
    planner = TaskPlanner()

    intent = Intent(
        name="UNKNOWN_INTENT",
        adapter="None",
        method="none",
        entities={}
    )

    state = {}

    with pytest.raises(ValueError) as exc_info:
        await planner.generate_plan(intent, state)

    assert "Unsupported intent" in str(exc_info.value)

@pytest.mark.asyncio
async def test_repair_plan_not_supported(sample_plan):
    planner = TaskPlanner()
    failed_action = sample_plan.actions[0]

    new_plan = await planner.repair_plan(
        failed_plan=sample_plan,
        failed_action=failed_action,
        decision=RecoveryDecision.NOT_SUPPORTED,
    )

    # Should replace the failing action with a notification
    assert len(new_plan.actions) == 2
    assert new_plan.actions[0].adapter == "notification"
    assert new_plan.actions[0].method == "send"
    assert "Unsupported action replaced with notification" in new_plan.actions[0].params["reason"]
    # The second action should remain unchanged
    assert new_plan.actions[1] == sample_plan.actions[1]

@pytest.mark.asyncio
async def test_repair_plan_permission_inserts_approval(sample_plan):
    planner = TaskPlanner()
    failed_action = sample_plan.actions[1]

    new_plan = await planner.repair_plan(
        failed_plan=sample_plan,
        failed_action=failed_action,
        decision=RecoveryDecision.PERMISSION,
    )

    # Should insert a HITL approval step before the failing action
    assert len(new_plan.actions) == 3
    approval_action = new_plan.actions[1]
    assert approval_action.adapter == "HITL"
    assert approval_action.method == "request_approval"
    assert approval_action.params["original_step"] == 1
    assert approval_action.params["reason"] == "User approval required for this action"

    # The failing action should now be at index 2
    assert new_plan.actions[2] == failed_action

@pytest.mark.asyncio
async def test_repair_plan_unrecoverable_returns_none(sample_plan):
    planner = TaskPlanner()
    failed_action = sample_plan.actions[0]

    result = await planner.repair_plan(
        failed_plan=sample_plan,
        failed_action=failed_action,
        decision=RecoveryDecision.UNKNOWN,  # unrecoverable
    )

    assert result is None