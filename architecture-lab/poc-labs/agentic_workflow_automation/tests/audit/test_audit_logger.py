import json
from unittest.mock import patch

from automation_app.audit.audit_logger import AuditLogger


def test_audit_logger_logs_correct_json_structure():
    workflow_id = "wf-123"
    event_type = "PLAN_CREATED"
    payload = {"foo": "bar", "x": 1}

    with patch("automation_app.audit.audit_logger.logger") as mock_logger:
        AuditLogger.log(workflow_id, event_type, payload)

        # Ensure logger.info was called exactly once
        mock_logger.info.assert_called_once()

        # Extract the logged JSON string
        logged_str = mock_logger.info.call_args[0][0]
        record = json.loads(logged_str)

        # Validate structure
        assert record["workflow_id"] == workflow_id
        assert record["event_type"] == event_type
        assert record["payload"] == payload

        # Timestamp should exist and be ISO‑8601 formatted
        assert "timestamp" in record
        assert isinstance(record["timestamp"], str)
        assert "T" in record["timestamp"]  # basic ISO‑8601 sanity check


def test_audit_logger_preserves_payload_exactly():
    payload = {"nested": {"a": 1, "b": [1, 2, 3]}, "flag": True}

    with patch("automation_app.audit.audit_logger.logger") as mock_logger:
        AuditLogger.log("wf", "EVENT", payload)

        logged_str = mock_logger.info.call_args[0][0]
        record = json.loads(logged_str)

        assert record["payload"] == payload


def test_audit_logger_uses_json_serialization():
    with patch("automation_app.audit.audit_logger.logger") as mock_logger:
        AuditLogger.log("wf", "EVENT", {"a": 1})

        logged_str = mock_logger.info.call_args[0][0]

        # Must be valid JSON
        parsed = json.loads(logged_str)
        assert isinstance(parsed, dict)
