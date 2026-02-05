import pytest
import json
from unittest.mock import MagicMock, patch, ANY
from automation_app.audit.audit_logger import AuditLogger, logger
from automation_app.models.plan import Plan


# --- Fixtures ---

@pytest.fixture
def mock_logger():
    """Intercepts the logger.info call."""
    with patch.object(logger, 'info') as mocked:
        yield mocked


@pytest.fixture
def mock_scrubber():
    """Mocks the PIIScrubber to control scrubbing output."""
    with patch('automation_app.audit.audit_logger.PIIScrubber') as mocked_class:
        instance = mocked_class.return_value
        # Default behavior: just return the data as is unless specified
        instance.scrub_data.side_effect = lambda x: {k: "***" for k in x.keys()}
        yield instance


## --- Tests ---

def test_log_formats_json_correctly(mock_logger):
    """Verifies that the log method produces a valid JSON string with required keys."""
    workflow_id = "test-wf-123"
    event_type = "TEST_EVENT"
    payload = {"key": "value"}

    AuditLogger.log(workflow_id, event_type, payload)

    # Check that info() was called once
    mock_logger.assert_called_once()

    # Parse the string passed to logger.info
    log_arg = mock_logger.call_args[0][0]
    log_data = json.loads(log_arg)

    assert log_data["workflow_id"] == workflow_id
    assert log_data["event_type"] == event_type
    assert log_data["payload"] == payload
    assert "timestamp" in log_data
    # Ensure it's valid ISO format
    assert "T" in log_data["timestamp"]


def test_log_plan_scrubs_pii(mock_logger, mock_scrubber):
    """Verifies that log_plan iterates through actions and calls the scrubber."""
    session_id = "sess-999"

    # Mock a Plan with actions
    mock_action = MagicMock()
    mock_action.adapter = "email_service"
    mock_action.method = "send"
    mock_action.params = {"to": "user@example.com", "body": "secret"}

    mock_plan = MagicMock(spec=Plan)
    mock_plan.actions = [mock_action]

    AuditLogger.log_plan(session_id, mock_plan)

    # Verify scrubber was called with action params
    mock_scrubber.scrub_data.assert_called_once_with({"to": "user@example.com", "body": "secret"})

    # Verify the final log call
    log_arg = mock_logger.call_args[0][0]
    log_data = json.loads(log_arg)

    expected_actions = [{
        "adapter": "email_service",
        "method": "send",
        "params": {"to": "***", "body": "***"}
    }]

    assert log_data["event_type"] == "PLAN_GENERATED"
    assert log_data["payload"]["actions"] == expected_actions


@pytest.mark.parametrize("payload", [
    ({"simple": "data"}),
    ({"nested": {"list": [1, 2, 3]}}),
    ({})
])
def test_log_various_payloads(mock_logger, payload):
    """Ensures various dictionary structures are correctly serialized."""
    AuditLogger.log("id", "TYPE", payload)

    log_arg = mock_logger.call_args[0][0]
    log_data = json.loads(log_arg)
    assert log_data["payload"] == payload


def test_log_plan_empty_actions(mock_logger):
    """Ensures logging a plan with no actions doesn't crash."""
    mock_plan = MagicMock(spec=Plan)
    mock_plan.actions = []

    AuditLogger.log_plan("empty-sess", mock_plan)

    log_arg = mock_logger.call_args[0][0]
    log_data = json.loads(log_arg)
    assert log_data["payload"]["actions"] == []