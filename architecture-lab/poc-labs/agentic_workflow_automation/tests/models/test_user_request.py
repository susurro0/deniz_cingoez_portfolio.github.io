# tests/models/test_user_request.py

import pytest
from pydantic import ValidationError

from automation_app.models.user_request import UserRequest


def test_user_request_creation():
    req = UserRequest(session_id="abc123", text="Hello world")
    assert req.session_id == "abc123"
    assert req.text == "Hello world"


@pytest.mark.parametrize(
    "payload,missing_field",
    [
        ({"text": "Hello"}, "session_id"),
        ({"session_id": "abc123"}, "text"),
        ({}, "session_id"),  # first missing field reported
    ],
)
def test_user_request_missing_fields(payload, missing_field):
    with pytest.raises(ValidationError) as exc:
        UserRequest(**payload)
    assert missing_field in str(exc.value)


@pytest.mark.parametrize(
    "payload",
    [
        {"session_id": 123, "text": "Hello"},          # session_id must be str
        {"session_id": "abc123", "text": 999},         # text must be str
        {"session_id": ["not", "a", "string"], "text": "Hello"},
    ],
)
def test_user_request_invalid_types(payload):
    with pytest.raises(ValidationError):
        UserRequest(**payload)


def test_user_request_serialization_round_trip():
    data = {"session_id": "abc123", "text": "Hello"}
    req = UserRequest(**data)
    assert req.model_dump() == data


def test_user_request_equality():
    a = UserRequest(session_id="abc", text="Hi")
    b = UserRequest(session_id="abc", text="Hi")
    assert a == b
