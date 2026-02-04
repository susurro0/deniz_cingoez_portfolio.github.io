import pytest

from automation_app.adapters.base_adapter import EnterpriseAdapter


def test_enterprise_adapter_cannot_be_instantiated():
    with pytest.raises(TypeError):
        EnterpriseAdapter()


def test_concrete_adapter_executes():
    class DummyAdapter(EnterpriseAdapter):
        def execute(self, action: str, params: dict) -> dict:
            return {"action": action, "params": params}

    adapter = DummyAdapter()
    result = adapter.execute("test", {"x": 1})
    assert result == {"action": "test", "params": {"x": 1}}


def test_abstract_method_body_executes():
    class DummyAdapter(EnterpriseAdapter):
        def execute(self, action: str, params: dict) -> dict:
            return super().execute(action, params)

    adapter = DummyAdapter()

    with pytest.raises(NotImplementedError):
        adapter.execute("x", {})
