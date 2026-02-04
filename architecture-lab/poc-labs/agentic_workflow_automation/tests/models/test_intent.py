# tests/models/test_intent.py

import pytest
from pydantic import ValidationError

from automation_app.models.intent import Intent


def test_intent_creation():
    intent = Intent(type="PTO", entity="Friday")
    assert intent.type == "PTO"
    assert intent.entity == "Friday"


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        ({"type": "PTO"}, "entity"),
        ({"entity": "Friday"}, "type"),
        ({}, "type"),  # both missing, Pydantic reports the first missing
    ],
)
def test_intent_missing_required_fields(payload, missing_field):
    with pytest.raises(ValidationError) as exc:
        Intent(**payload)
    assert missing_field in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"type": 123, "entity": "Friday"},
        {"type": "PTO", "entity": 999},
        {"type": ["PTO"], "entity": "Friday"},
    ],
)
def test_intent_invalid_types(payload):
    with pytest.raises(ValidationError):
        Intent(**payload)


def test_intent_rejects_extra_fields():
    with pytest.raises(ValidationError):
        Intent(type="PTO", entity="Friday", extra="boom")


def test_intent_serialization_round_trip():
    data = {"type": "PTO", "entity": "Friday"}
    intent = Intent(**data)
    assert intent.model_dump() == data


def test_intent_equality():
    a = Intent(type="PTO", entity="Friday")
    b = Intent(type="PTO", entity="Friday")
    assert a == b
