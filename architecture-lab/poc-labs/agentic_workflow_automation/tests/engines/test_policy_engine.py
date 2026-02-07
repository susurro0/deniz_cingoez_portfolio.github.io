from unittest.mock import MagicMock, AsyncMock

import pytest
from types import SimpleNamespace

from automation_app.engines.policy_engine import PolicyEngine
from automation_app.models.action import Action
from automation_app.models.plan import Plan


# Mocking the Plan object for validate_plan tests
class MockPlan:
    def __init__(self, actions):
        self.actions = actions


@pytest.fixture
def engine():
    rules = [
        {
            "id": "WD-ALLOW-HR-PTO",
            "effect": "allow",
            "target": {
                "adapter": "Workday",
                "method": "create_time_off",
            },
            "conditions": {
                "roles": ["HR", "Manager"],
                "departments": ["Engineering"],
            },
        },
        {
            "id": "MSG-ALLOW-EMAIL",
            "effect": "allow",
            "target": {
                "adapter": "MSGraph",
                "method": "send_email",
            },
            "conditions": {
                "roles": ["Employee"],
            },
        },
    ]
    return PolicyEngine(rules)


@pytest.mark.asyncio
async def test_check_permissions_success(engine):
    context = {"role": "HR", "department": "Engineering"}

    result = await engine.check_permissions(
        "user123", "Workday.create_time_off", context
    )

    assert result is True


@pytest.mark.asyncio
async def test_check_permissions_wrong_role(engine):
    context = {"role": "Employee", "department": "Engineering"}

    result = await engine.check_permissions(
        "user123", "Workday.create_time_off", context
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_permissions_wrong_dept(engine):
    context = {"role": "HR", "department": "Sales"}

    result = await engine.check_permissions(
        "user123", "Workday.create_time_off", context
    )

    assert result is False


@pytest.mark.asyncio
async def test_deny_by_default(engine):
    context = {"role": "Admin", "department": "IT"}

    result = await engine.check_permissions(
        "user123", "Slack.post_message", context
    )

    assert result is False


@pytest.mark.asyncio
async def test_validate_plan_mixed_results(engine):
    action1 = SimpleNamespace(adapter="MSGraph", method="send_email")
    action2 = SimpleNamespace(adapter="Workday", method="create_time_off")

    plan = MockPlan(actions=[action1, action2])
    context = {"role": "Employee", "department": "Engineering"}

    result = await engine.validate_plan(plan, context)

    assert result is False


@pytest.mark.asyncio
async def test_malformed_action_string(engine):
    result = await engine.check_permissions(
        "user123", "JustAMethodNameNoDot", {}
    )

    assert result is False


@pytest.mark.asyncio
async def test_continue_branch_hit():
    rules = [
        {
            "id": "WD-DENY-HR",
            "effect": "deny",
            "target": {
                "adapter": "Workday",
                "method": "create_time_off",
            },
            "conditions": {
                "roles": ["HR"],
            },
        },
        {
            "id": "WD-ALLOW-EMPLOYEE",
            "effect": "allow",
            "target": {
                "adapter": "Workday",
                "method": "create_time_off",
            },
            "conditions": {
                "roles": ["Employee"],
            },
        },
    ]

    engine = PolicyEngine(rules)
    context = {"role": "Employee", "department": "Engineering"}

    result = await engine.check_permissions(
        "user123", "Workday.create_time_off", context
    )

    assert result is True


@pytest.mark.asyncio
async def test_continue_branch_no_rule_allows():
    rules = [
        {
            "id": "WD-ALLOW-HR",
            "effect": "allow",
            "target": {
                "adapter": "Workday",
                "method": "create_time_off",
            },
            "conditions": {
                "roles": ["HR"],
            },
        },
        {
            "id": "WD-ALLOW-MANAGER",
            "effect": "allow",
            "target": {
                "adapter": "Workday",
                "method": "create_time_off",
            },
            "conditions": {
                "roles": ["Manager"],
            },
        },
    ]

    engine = PolicyEngine(rules)
    context = {"role": "Employee"}

    result = await engine.check_permissions(
        "user123", "Workday.create_time_off", context
    )

    assert result is False


@pytest.mark.asyncio
async def test_validate_plan_all_actions_allowed():
    # Arrange
    auditor = MagicMock()
    engine = PolicyEngine(auditor=auditor)

    # Create a real plan with real Action objects
    plan = Plan(
        actions=[
            Action(adapter="TestAdapter", method="do_it", params={"x": 1}),
            Action(adapter="TestAdapter", method="do_more", params={"y": 2}),
        ]
    )

    # Mock _is_action_allowed to always allow
    engine._is_action_allowed = AsyncMock(return_value=(True, ["rule1"]))

    # Act
    result = await engine.validate_plan(plan, user_context={"user_id": "u1"})

    # Assert
    assert result is True
    engine._is_action_allowed.assert_awaited()
    auditor.log.assert_not_called()  # No violations → no audit logs

@pytest.mark.asyncio
async def test_validate_plan_empty_plan_returns_true():
    engine = PolicyEngine(auditor=MagicMock())
    plan = Plan(actions=[])
    result = await engine.validate_plan(plan)
    assert result is True

@pytest.mark.asyncio
async def test_is_action_allowed_superuser_bypass():
    auditor = MagicMock()
    engine = PolicyEngine(auditor=auditor)
    engine.rules = [{"id": "R1"}]  # irrelevant, bypass happens first

    action = Action(adapter="A", method="m", params={})
    allowed, rules = await engine._is_action_allowed(
        action,
        user_context={"role": "SuperUser"}
    )

    assert allowed is True
    assert rules == ["SUPERUSER_BYPASS"]

@pytest.mark.asyncio
async def test_is_action_allowed_no_rules():
    auditor = MagicMock()
    engine = PolicyEngine(auditor=auditor)
    engine.rules = []  # no rules

    action = Action(adapter="A", method="m", params={})
    allowed, rules = await engine._is_action_allowed(
        action,
        user_context={"role": "Employee"}
    )

    assert allowed is False
    assert rules == []

@pytest.mark.asyncio
async def test_is_action_allowed_deny_rule():
    auditor = MagicMock()
    engine = PolicyEngine(auditor=auditor)

    engine.rules = [
        {
            "id": "DENY1",
            "target": {"adapter": "A", "method": "m"},
            "effect": "deny",
            "conditions": {
                "roles": ["Employee"],
                "departments": ["Engineering"]
            }
        }
    ]

    action = Action(adapter="A", method="m", params={})
    allowed, rules = await engine._is_action_allowed(
        action,
        user_context={"role": "Employee", "department": "Engineering"}
    )

    assert allowed is False
    assert rules == ["DENY1"]
