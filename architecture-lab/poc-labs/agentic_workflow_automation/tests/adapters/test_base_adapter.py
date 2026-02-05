import pytest
from automation_app.adapters.base_adapter import EnterpriseAdapter


# ---------------------------------------------------------------------------
# Base class cannot be instantiated
# ---------------------------------------------------------------------------

def test_enterprise_adapter_cannot_be_instantiated():
    with pytest.raises(TypeError):
        EnterpriseAdapter()


# ---------------------------------------------------------------------------
# Fully implemented subclass
# ---------------------------------------------------------------------------

class FullAdapter(EnterpriseAdapter):
    def execute(self, action: str, params: dict) -> dict:
        return {"executed": action, "params": params}

    def compensate(self, action: str, params: dict, result: dict) -> None:
        self.compensated = (action, params, result)

    def supported_actions(self) -> set[str]:
        return {"create", "delete"}


def test_full_adapter_instantiation():
    adapter = FullAdapter()
    assert isinstance(adapter, EnterpriseAdapter)


def test_full_adapter_execute():
    adapter = FullAdapter()
    result = adapter.execute("create", {"x": 1})
    assert result == {"executed": "create", "params": {"x": 1}}


def test_full_adapter_compensate():
    adapter = FullAdapter()
    adapter.compensate("delete", {"id": 10}, {"status": "ok"})
    assert adapter.compensated == ("delete", {"id": 10}, {"status": "ok"})


def test_full_adapter_supported_actions():
    adapter = FullAdapter()
    assert adapter.supported_actions() == {"create", "delete"}


# ---------------------------------------------------------------------------
# Missing execute()
# ---------------------------------------------------------------------------

class MissingExecute(EnterpriseAdapter):
    def compensate(self, action: str, params: dict, result: dict) -> None:
        pass

    def supported_actions(self) -> set[str]:
        return {"x"}


def test_missing_execute_raises_type_error():
    with pytest.raises(TypeError):
        MissingExecute()


# ---------------------------------------------------------------------------
# Missing compensate()
# ---------------------------------------------------------------------------

class MissingCompensate(EnterpriseAdapter):
    def execute(self, action: str, params: dict) -> dict:
        return {}

    def supported_actions(self) -> set[str]:
        return {"x"}


def test_missing_compensate_raises_type_error():
    with pytest.raises(TypeError):
        MissingCompensate()


# ---------------------------------------------------------------------------
# Missing supported_actions()
# ---------------------------------------------------------------------------

class MissingSupportedActions(EnterpriseAdapter):
    def execute(self, action: str, params: dict) -> dict:
        return {}

    def compensate(self, action: str, params: dict, result: dict) -> None:
        pass


def test_missing_supported_actions_raises_type_error():
    with pytest.raises(TypeError):
        MissingSupportedActions()


# ---------------------------------------------------------------------------
# Abstract method body should raise NotImplementedError
# ---------------------------------------------------------------------------

class CallsSuper(EnterpriseAdapter):
    def execute(self, action: str, params: dict) -> dict:
        return super().execute(action, params)

    def compensate(self, action: str, params: dict, result: dict) -> None:
        return super().compensate(action, params, result)

    def supported_actions(self) -> set[str]:
        return super().supported_actions()


@pytest.mark.parametrize(
    "method, args",
    [
        ("execute", ("x", {})),
        ("compensate", ("x", {}, {})),
        ("supported_actions", ()),
    ],
    ids=["execute", "compensate", "supported_actions"],
)
def test_abstract_method_body_raises_not_implemented(method, args):
    adapter = CallsSuper()
    with pytest.raises(NotImplementedError):
        getattr(adapter, method)(*args)
