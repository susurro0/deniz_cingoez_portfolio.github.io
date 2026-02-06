import pytest
from pydantic import ValidationError

from automation_app.models.intent import Intent


def test_intent_creation():
    intent = Intent(
        name="REQUEST_TIME_OFF",
        adapter="Workday",
        method="create_time_off",
        entities={"date": "Friday"},
    )

    assert intent.name == "REQUEST_TIME_OFF"
    assert intent.adapter == "Workday"
    assert intent.method == "create_time_off"
    assert intent.entities == {"date": "Friday"}


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        (
            {"adapter": "Workday", "method": "create_time_off"},
            "name",
        ),
        (
            {"name": "REQUEST_TIME_OFF", "method": "create_time_off"},
            "adapter",
        ),
        (
            {"name": "REQUEST_TIME_OFF", "adapter": "Workday"},
            "method",
        ),
        ({}, "name"),  # first missing field Pydantic reports
    ],
)
def test_intent_missing_required_fields(payload, missing_field):
    with pytest.raises(ValidationError) as exc:
        Intent(**payload)

    assert missing_field in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": 123,
            "adapter": "Workday",
            "method": "create_time_off",
        },
        {
            "name": "REQUEST_TIME_OFF",
            "adapter": 456,
            "method": "create_time_off",
        },
        {
            "name": "REQUEST_TIME_OFF",
            "adapter": "Workday",
            "method": ["create_time_off"],
        },
        {
            "name": "REQUEST_TIME_OFF",
            "adapter": "Workday",
            "method": "create_time_off",
            "entities": "Friday",
        },
    ],
)
def test_intent_invalid_types(payload):
    with pytest.raises(ValidationError):
        Intent(**payload)


def test_intent_rejects_extra_fields():
    with pytest.raises(ValidationError):
        Intent(
            name="REQUEST_TIME_OFF",
            adapter="Workday",
            method="create_time_off",
            extra="boom",
        )


def test_intent_serialization_round_trip():
    data = {
        "name": "REQUEST_TIME_OFF",
        "adapter": "Workday",
        "method": "create_time_off",
        "entities": {"date": "Friday"},
    }

    intent = Intent(**data)
    assert intent.model_dump() == data


def test_intent_equality():
    a = Intent(
        name="REQUEST_TIME_OFF",
        adapter="Workday",
        method="create_time_off",
        entities={"date": "Friday"},
    )
    b = Intent(
        name="REQUEST_TIME_OFF",
        adapter="Workday",
        method="create_time_off",
        entities={"date": "Friday"},
    )

    assert a == b
