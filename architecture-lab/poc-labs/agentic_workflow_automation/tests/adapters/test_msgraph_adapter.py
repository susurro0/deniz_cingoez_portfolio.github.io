# tests/adapters/test_msgraph_adapter.py

import pytest
from automation_app.adapters.msgraph_adapter import MSGraphAdapter


def test_msgraph_check_calendar_availability():
    adapter = MSGraphAdapter()

    result = adapter.execute(
        action="check_calendar_availability",
        params={"date": "Friday"}
    )

    assert isinstance(result, dict)
    assert result == {"status": "available"}


def test_msgraph_unknown_action_raises():
    adapter = MSGraphAdapter()

    with pytest.raises(ValueError) as exc:
        adapter.execute("nonexistent_action", {})

    assert "Unknown MSGraph action" in str(exc.value)
    assert "nonexistent_action" in str(exc.value)
