from automation_app.models.executed_step import ExecutedStep


def test_executed_step_minimal():
    step = ExecutedStep(
        adapter_name="Workday",
        method="create_user",
        params={"name": "Alice"},
    )

    assert step.adapter_name == "Workday"
    assert step.method == "create_user"
    assert step.params == {"name": "Alice"}
    assert step.result is None


def test_executed_step_with_result():
    result = {"status": "ok", "id": 123}
    step = ExecutedStep(
        adapter_name="MSGraph",
        method="send_email",
        params={"to": "bob@example.com"},
        result=result,
    )

    assert step.result == result


def test_executed_step_preserves_nested_structures():
    params = {"a": 1, "nested": {"x": 10}}
    result = {"r": [1, 2, 3]}

    step = ExecutedStep(
        adapter_name="Adapter",
        method="do",
        params=params,
        result=result,
    )

    assert step.params["nested"]["x"] == 10
    assert step.result["r"] == [1, 2, 3]


def test_executed_step_equality():
    a = ExecutedStep("A", "m", {"x": 1}, {"y": 2})
    b = ExecutedStep("A", "m", {"x": 1}, {"y": 2})
    c = ExecutedStep("A", "m", {"x": 2}, {"y": 2})

    assert a == b
    assert a != c


def test_executed_step_repr_contains_fields():
    step = ExecutedStep("Adapter", "run", {"foo": "bar"}, {"ok": True})
    text = repr(step)

    assert "Adapter" in text
    assert "run" in text
    assert "foo" in text
    assert "ok" in text
