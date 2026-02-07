# tests/api/test_orchestrator_routes.py

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from automation_app.api.routes.orchestrator_routes import OrchestratorRoutes
from automation_app.models.workflow_state import WorkflowState


def create_test_app():
    orchestrator = AsyncMock()

    # Default async return values
    orchestrator.process_request.return_value = "Processed OK"
    orchestrator.propose.return_value = {
        "message": "Plan proposed",
        "state": WorkflowState.PROPOSED.name,  # Serialize for JSON
        "plan": {"foo": "bar"}
    }
    orchestrator.confirm.return_value = {
        "message": "Execution completed",
        "state": WorkflowState.COMPLETED.name
    }
    orchestrator.reject.return_value = {
        "message": "Plan rejected by user",
        "state": WorkflowState.REJECTED.name
    }

    routes = OrchestratorRoutes(orchestrator)
    app = FastAPI()
    app.include_router(routes.router)
    client = TestClient(app)  # <- wrap app in TestClient

    return client, orchestrator


# ---------------------------------------------------------------------------
# /process
# ---------------------------------------------------------------------------

def test_process_route_success():
    app, orchestrator = create_test_app()

    payload = {
        "session_id": "s1",
        "text": "Book PTO for Friday",
        "role": "Manager",
        "department": "Engineering"
    }

    response = app.post("/process", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Processed OK", 'plan': None, 'state': None}

    orchestrator.process_request.assert_awaited_once_with(
        user_input='Book PTO for Friday', session_id='s1', user_id='anonymous', role='Manager', department='Engineering'
    )



def test_process_route_validation_error():
    client, _ = create_test_app()

    # Missing "text"
    response = client.post("/process", json={"session_id": "s1"})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /propose
# ---------------------------------------------------------------------------

def test_propose_success():
    client, orchestrator = create_test_app()

    payload = {
        "session_id": "s1",
        "text": "Book PTO for Friday",
        "role": "Manager",
        "department": "Engineering"
    }

    response = client.post("/propose", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Plan proposed",
        "state": WorkflowState.PROPOSED,
        "plan": {"foo": "bar"}
    }

    orchestrator.propose.assert_called_once_with(
        user_input='Book PTO for Friday', session_id='s1', user_id='anonymous', role='Manager', department='Engineering'
    )


def test_propose_route_validation_error():
    client, _ = create_test_app()

    response = client.post("/propose", json={"session_id": "s1"})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /confirm
# ---------------------------------------------------------------------------

def test_confirm_route_success():
    client, orchestrator = create_test_app()

    payload = {"session_id": "s1", "text": "ignored"}

    response = client.post("/confirm", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Execution completed",
        "state": WorkflowState.COMPLETED,
        "plan": None
    }

    orchestrator.confirm.assert_called_once_with("s1")


def test_confirm_route_validation_error():
    client, _ = create_test_app()

    # Missing session_id
    response = client.post("/confirm", json={"text": "ignored"})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /reject
# ---------------------------------------------------------------------------

def test_reject_route_success():
    client, orchestrator = create_test_app()

    orchestrator.reject.return_value = {
        "message": "Plan rejected by user",
        "state": WorkflowState.REJECTED
    }

    payload = {"session_id": "s1", "text": "ignored"}

    response = client.post("/reject", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Plan rejected by user",
        "state": WorkflowState.REJECTED,
        "plan": None
    }

    orchestrator.reject.assert_called_once_with("s1")


def test_reject_route_wrong_state():
    client, orchestrator = create_test_app()

    orchestrator.reject.return_value = {
        "message": "Nothing to reject",
        "state": WorkflowState.EXECUTING
    }

    payload = {"session_id": "s1", "text": "ignored"}

    response = client.post("/reject", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Nothing to reject",
        "state": WorkflowState.EXECUTING,
        "plan": None
    }

    orchestrator.reject.assert_called_once_with("s1")


def test_reject_route_validation_error():
    client, _ = create_test_app()

    # Missing session_id
    response = client.post("/reject", json={"text": "ignored"})

    assert response.status_code == 422
