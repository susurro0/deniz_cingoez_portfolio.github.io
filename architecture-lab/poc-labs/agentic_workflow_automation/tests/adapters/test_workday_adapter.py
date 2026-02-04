import pytest
from automation_app.adapters.workday_adapter import WorkdayAdapter


def test_workday_execute_book_time_off_success():
    # Arrange
    adapter = WorkdayAdapter()
    action = "book_time_off"
    params = {"days": 2, "start_date": "2024-01-01"}

    # Act
    result = adapter.execute(action, params)

    # Assert
    assert result["status"] == "success"
    assert result["reference"] == "WD-123"


def test_workday_execute_invalid_action_raises_error():
    # Arrange
    adapter = WorkdayAdapter()
    invalid_action = "order_pizza"

    # Act & Assert
    with pytest.raises(ValueError) as excinfo:
        adapter.execute(invalid_action, {})

    assert "Unknown Workday action" in str(excinfo.value)