import pytest
from types import SimpleNamespace

from automation_app.engines.policy_engine import PolicyEngine


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
