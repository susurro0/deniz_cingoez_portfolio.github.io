# tests/models/test_orchestrator_response.py

import pytest
from pydantic import ValidationError

from automation_app.models.orchestrator_response import OrchestratorResponse


def test_orchestrator_response_creation():
    resp = OrchestratorResponse(message="Operation completed")
    assert resp.message == "Operation completed"


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        ({}, "message"),
    ],
)
def test_orchestrator_response_missing_field(payload, missing_field):
    with pytest.raises(ValidationError) as exc:
        OrchestratorResponse(**payload)
    assert missing_field in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"message": 123},          # must be str
        {"message": ["not", "str"]},
    ],
)
def test_orchestrator_response_invalid_types(payload):
    with pytest.raises(ValidationError):
        OrchestratorResponse(**payload)


def test_orchestrator_response_serialization_round_trip():
    data = {"message": "Done"}
    resp = OrchestratorResponse(**data)
    assert resp.model_dump() == data


def test_orchestrator_response_equality():
    a = OrchestratorResponse(message="Hello")
    b = OrchestratorResponse(message="Hello")
    assert a == b
