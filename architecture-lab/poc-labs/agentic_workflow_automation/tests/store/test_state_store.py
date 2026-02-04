# tests/state/test_state_store.py
from automation_app.store.state_store import StateStore


def test_save_and_get_context():
    store = StateStore()

    store.save_context("session1", {"foo": "bar"})
    result = store.get_context("session1")

    assert result == {"foo": "bar"}


def test_get_context_returns_empty_when_missing():
    store = StateStore()

    result = store.get_context("unknown_session")

    assert result == {}  # default fallback


def test_overwrites_existing_context():
    store = StateStore()

    store.save_context("session1", {"foo": "bar"})
    store.save_context("session1", {"baz": 123})

    result = store.get_context("session1")

    assert result == {"baz": 123}
