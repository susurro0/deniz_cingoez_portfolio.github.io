# tests/models/test_plan.py

import pytest
from pydantic import ValidationError

from automation_app.models.plan import Plan
from automation_app.models.action import Action


# ---------------------------------------------------------------------------
# Valid plan creation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "actions, expected_len",
    [
        ([], 0),
        (
            [
                Action(adapter="Workday", method="get_employee", params={"id": 1}),
                Action(adapter="MSGraph", method="send_mail", params={"to": "x@y.com"}),
            ],
            2,
        ),
    ],
)
def test_plan_creation(actions, expected_len):
    plan = Plan(actions=actions)

    assert len(plan.actions) == expected_len


# ---------------------------------------------------------------------------
# Default / optional behavior
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "input_kwargs, expected_actions",
    [
        ({}, []),             # missing actions field
        ({"actions": []}, []), # explicitly empty
    ],
)
def test_plan_default_actions(input_kwargs, expected_actions):
    plan = Plan(**input_kwargs)

    assert plan.actions == expected_actions


# ---------------------------------------------------------------------------
# Invalid inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "input_data",
    [
        {"actions": "not-a-list"},                # wrong type
        {"actions": [{"adapter": "Workday"}]},    # invalid action shape
        {"actions": [], "extra": "boom"},         # extra field not allowed
    ],
    ids=[
        "actions-not-a-list",
        "invalid-action-inside-list",
        "extra-field-rejected",
    ],
)
def test_plan_invalid_inputs(input_data):
    with pytest.raises(ValidationError):
        Plan(**input_data)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_plan_serialization_round_trip():
    data = {
        "actions": [
            {
                "adapter": "Workday",
                "method": "get_employee",
                "params": {"id": 1},
            }
        ]
    }

    plan = Plan(**data)

    assert plan.model_dump() == data


# ---------------------------------------------------------------------------
# Equality
# ---------------------------------------------------------------------------

def test_plan_equality():
    a = Plan(actions=[Action(adapter="A", method="m", params={})])
    b = Plan(actions=[Action(adapter="A", method="m", params={})])

    assert a == b
