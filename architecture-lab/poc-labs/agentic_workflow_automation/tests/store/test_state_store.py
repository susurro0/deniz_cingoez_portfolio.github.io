# tests/store/test_state_store.py

from automation_app.store.state_store import StateStore
from automation_app.models.workflow_state import WorkflowState


def test_save_and_get_context_with_default_state():
    store = StateStore()

    store.save_context("session1", {"foo": "bar"})
    result = store.get_context("session1")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["data"] == {"foo": "bar"}


def test_save_and_get_context_with_explicit_state():
    store = StateStore()

    store.save_context(
        "session1",
        {"foo": "bar"},
        state=WorkflowState.CONFIRMED
    )
    result = store.get_context("session1")

    assert result["state"] == WorkflowState.CONFIRMED
    assert result["data"] == {"foo": "bar"}


def test_get_context_returns_default_when_missing():
    store = StateStore()

    result = store.get_context("unknown")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["data"] == {}


def test_overwrites_existing_context():
    store = StateStore()

    store.save_context("session1", {"foo": "bar"}, WorkflowState.PROPOSED)
    store.save_context("session1", {"baz": 123}, WorkflowState.EXECUTING)

    result = store.get_context("session1")

    assert result["state"] == WorkflowState.EXECUTING
    assert result["data"] == {"baz": 123}
