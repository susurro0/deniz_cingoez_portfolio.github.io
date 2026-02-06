# tests/models/test_policy_engine.py
import pytest

from automation_app.engines.policy_engine import PolicyEngine
from automation_app.models.plan import Plan
from automation_app.models.action import Action

@pytest.mark.asyncio
async def test_validate_plan_passes_when_first_action_is_calendar_check():
    engine = PolicyEngine()
    plan = Plan(actions=[
        Action(
            adapter="Workday",
            method="check_calendar_availability",
            params={"date": "2025-01-01"}
        )
    ])

    assert await engine.validate_plan(plan) is True

@pytest.mark.asyncio
async def test_validate_plan_fails_when_no_actions():
    engine = PolicyEngine()
    plan = Plan(actions=[])

    assert await engine.validate_plan(plan) is False


@pytest.mark.asyncio
async def test_validate_plan_fails_when_first_action_is_not_calendar_check():
    engine = PolicyEngine()
    plan = Plan(actions=[
        Action(
            adapter="Workday",
            method="submit_pto_request",
            params={"date": "2025-01-01"}
        )
    ])

    assert await engine.validate_plan(plan) is False


@pytest.mark.asyncio
async def test_validate_plan_only_checks_first_action():
    engine = PolicyEngine()
    plan = Plan(actions=[
        Action(
            adapter="Workday",
            method="check_calendar_availability",
            params={}
        ),
        Action(
            adapter="Workday",
            method="submit_pto_request",
            params={}
        )
    ])

    # Should pass because the FIRST action is correct
    assert await engine.validate_plan(plan) is True


@pytest.mark.asyncio
async def test_check_permissions_always_allows():
    engine = PolicyEngine()
    assert await engine.check_permissions("user123", "any_action") is True
