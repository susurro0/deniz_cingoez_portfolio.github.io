import pytest
from types import SimpleNamespace
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan
from automation_app.models.action import Action
from automation_app.engines.task_planner import TaskPlanner


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
