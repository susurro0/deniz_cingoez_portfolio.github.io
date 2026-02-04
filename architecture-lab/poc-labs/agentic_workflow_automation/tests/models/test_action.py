# tests/models/test_action.py

import pytest
from pydantic import ValidationError

from automation_app.models.action import Action


def test_action_creation():
    action = Action(
        adapter="Workday",
        method="get_employee",
        params={"employee_id": 123}
    )
    assert action.adapter == "Workday"
    assert action.method == "get_employee"
    assert action.params == {"employee_id": 123}


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        ({"method": "get_employee", "params": {}}, "adapter"),
        ({"adapter": "Workday", "params": {}}, "method"),
        ({"adapter": "Workday", "method": "get_employee"}, "params"),
        ({}, "adapter"),
    ],
)
def test_action_missing_required_fields(payload, missing_field):
    with pytest.raises(ValidationError) as exc:
        Action(**payload)
    assert missing_field in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"adapter": 123, "method": "get_employee", "params": {}},
        {"adapter": "Workday", "method": 999, "params": {}},
        {"adapter": "Workday", "method": "get_employee", "params": "not-a-dict"},
    ],
)
def test_action_invalid_types(payload):
    with pytest.raises(ValidationError):
        Action(**payload)


def test_action_rejects_extra_fields():
    with pytest.raises(ValidationError):
        Action(
            adapter="Workday",
            method="get_employee",
            params={},
            extra="boom"
        )


def test_action_serialization_round_trip():
    data = {
        "adapter": "Workday",
        "method": "get_employee",
        "params": {"employee_id": 123},
    }
    action = Action(**data)
    assert action.model_dump() == data


def test_action_equality():
    a = Action(adapter="Workday", method="get_employee", params={"x": 1})
    b = Action(adapter="Workday", method="get_employee", params={"x": 1})
    assert a == b
