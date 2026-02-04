# tests/engine/test_execution_engine.py

import pytest
from unittest.mock import MagicMock

from automation_app.engines.execution_engine import ExecutionEngine
from automation_app.models.plan import Plan
from automation_app.models.action import Action


def test_run_executes_all_actions_in_order():
    # Create mock adapters
    msgraph = MagicMock()
    workday = MagicMock()

    engine = ExecutionEngine(adapters={
        "MSGraph": msgraph,
        "Workday": workday,
    })

    plan = Plan(actions=[
        Action(adapter="MSGraph", method="check_calendar", params={"x": 1}),
        Action(adapter="Workday", method="book_pto", params={"y": 2}),
    ])

    result = engine.run(plan)

    assert result is True

    msgraph.execute.assert_called_once_with("check_calendar", {"x": 1})
    workday.execute.assert_called_once_with("book_pto", {"y": 2})


def test_run_raises_if_adapter_missing():
    engine = ExecutionEngine(adapters={})  # no adapters registered

    plan = Plan(actions=[
        Action(adapter="MSGraph", method="check_calendar", params={})
    ])

    with pytest.raises(ValueError) as exc:
        engine.run(plan)

    assert "No adapter registered for MSGraph" in str(exc.value)


def test_run_skips_no_actions_and_returns_true():
    engine = ExecutionEngine(adapters={})
    plan = Plan(actions=[])

    result = engine.run(plan)

    assert result is True  # nothing to execute, but still succeeds


def test_rollback_is_noop_for_now():
    engine = ExecutionEngine(adapters={})

    # Should not raise anything
    engine.rollback("step-1")
