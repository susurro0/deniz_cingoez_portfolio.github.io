# tests/store/test_state_store.py
import pytest

from automation_app.store.state_store import StateStore
from automation_app.models.workflow_state import WorkflowState

@pytest.mark.asyncio
async def test_save_and_get_context_with_default_state():
    store = StateStore()

    await store.save_context("session1", {"foo": "bar"})
    result = await store.get_context("session1")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["data"] == {"foo": "bar"}

@pytest.mark.asyncio
async def test_save_and_get_context_with_explicit_state():
    store = StateStore()

    await store.save_context(
        "session1",
        {"foo": "bar"},
        state=WorkflowState.CONFIRMED
    )
    result = await store.get_context("session1")

    assert result["state"] == WorkflowState.CONFIRMED
    assert result["data"] == {"foo": "bar"}


@pytest.mark.asyncio
async def test_get_context_returns_default_when_missing():
    store = StateStore()

    result = await store.get_context("unknown")

    assert result["state"] == WorkflowState.PROPOSED
    assert result["data"] == {}

@pytest.mark.asyncio
async def test_overwrites_existing_context():
    store = StateStore()

    await store.save_context("session1", {"foo": "bar"}, WorkflowState.PROPOSED)
    await store.save_context("session1", {"baz": 123}, WorkflowState.EXECUTING)

    result = await store.get_context("session1")

    assert result["state"] == WorkflowState.EXECUTING
    assert result["data"] == {"baz": 123}

@pytest.mark.asyncio
async def test_delete_session_existing():
    store = StateStore()
    store.storage["abc"] = {
        "state": WorkflowState.PROPOSED,
        "data": {"foo": "bar"},
    }

    await store.delete_session("abc")

    assert "abc" not in store.storage


@pytest.mark.asyncio
async def test_delete_session_nonexistent():
    store = StateStore()

    # Should not raise and should not modify storage
    await store.delete_session("missing")

    assert store.storage == {}
