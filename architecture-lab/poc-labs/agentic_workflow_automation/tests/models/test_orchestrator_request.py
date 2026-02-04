# tests/models/test_orchestrator_request.py

import pytest
from pydantic import ValidationError

from automation_app.models.orchestrator_request import OrchestratorRequest


def test_orchestrator_request_creation():
    req = OrchestratorRequest(session_id="session-1", text="Hello")
    assert req.session_id == "session-1"
    assert req.text == "Hello"


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        ({"text": "Hello"}, "session_id"),
        ({"session_id": "session-1"}, "text"),
        ({}, "session_id"),  # first missing field reported
    ],
)
def test_orchestrator_request_missing_fields(payload, missing_field):
    with pytest.raises(ValidationError) as exc:
        OrchestratorRequest(**payload)
    assert missing_field in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"session_id": 123, "text": "Hello"},          # session_id must be str
        {"session_id": "session-1", "text": 999},      # text must be str
        {"session_id": ["not", "a", "string"], "text": "Hello"},
    ],
)
def test_orchestrator_request_invalid_types(payload):
    with pytest.raises(ValidationError):
        OrchestratorRequest(**payload)


def test_orchestrator_request_serialization_round_trip():
    data = {"session_id": "session-1", "text": "Hello"}
    req = OrchestratorRequest(**data)
    assert req.model_dump() == data


def test_orchestrator_request_equality():
    a = OrchestratorRequest(session_id="s1", text="Hi")
    b = OrchestratorRequest(session_id="s1", text="Hi")
    assert a == b
