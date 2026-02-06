# tests/models/test_task_planner.py

import pytest

from automation_app.engines.task_planner import TaskPlanner
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan
from automation_app.models.action import Action


@pytest.mark.asyncio
async def test_generate_plan_for_pto():
    planner = TaskPlanner()
    intent = Intent(type="PTO", entity="Friday")

    plan = await planner.generate_plan(intent, state={})

    assert isinstance(plan, Plan)
    assert len(plan.actions) == 2

    first, second = plan.actions

    # First action
    assert isinstance(first, Action)
    assert first.adapter == "MSGraph"
    assert first.method == "check_calendar_availability"
    assert first.params == {"date": "Friday"}

    # Second action
    assert isinstance(second, Action)
    assert second.adapter == "Workday"
    assert second.method == "book_time_off"
    assert second.params == {"dates": ["Friday"]}

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent_type",
    ["Meeting", "Travel", "Sick", "Random"]
)
async def test_generate_plan_unsupported_intents(intent_type):
    planner = TaskPlanner()
    intent = Intent(type=intent_type, entity="Friday")

    with pytest.raises(ValueError) as exc:
        await planner.generate_plan(intent, state={})

    assert "Unsupported intent" in str(exc.value)


@pytest.mark.asyncio
async def test_generate_plan_ignores_state_for_now():
    planner = TaskPlanner()
    intent = Intent(type="PTO", entity="Friday")

    plan = await planner.generate_plan(intent, state={"foo": "bar"})

    # State is not used yet, but plan should still be correct
    assert len(plan.actions) == 2
