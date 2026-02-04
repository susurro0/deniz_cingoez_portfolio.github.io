# tests/api/test_orchestrator_routes.py

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from automation_app.api.routes.orchestrator_routes import OrchestratorRoutes
from automation_app.models.workflow_state import WorkflowState


def create_test_app():
    orchestrator = MagicMock()

    # Default mock return values
    orchestrator.process_request.return_value = "Processed OK"
    orchestrator.propose.return_value = {
        "message": "Plan proposed",
        "state": WorkflowState.PROPOSED,
        "plan": {"foo": "bar"}
    }
    orchestrator.confirm.return_value = {
        "message": "Execution completed",
        "state": WorkflowState.COMPLETED
    }

    routes = OrchestratorRoutes(orchestrator)

    app = FastAPI()
    app.include_router(routes.router)

    return TestClient(app), orchestrator


# ---------------------------------------------------------------------------
# /process
# ---------------------------------------------------------------------------

def test_process_route_success():
    client, orchestrator = create_test_app()

    payload = {"session_id": "s1", "text": "Hello"}

    response = client.post("/process", json=payload)

    assert response.status_code == 200
    assert response.json() == { "message": "Processed OK", "state": None, "plan": None }
    orchestrator.process_request.assert_called_once_with(
        user_input="Hello",
        session_id="s1"
    )


def test_process_route_validation_error():
    client, _ = create_test_app()

    # Missing "text"
    response = client.post("/process", json={"session_id": "s1"})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /propose
# ---------------------------------------------------------------------------

def test_propose_route_success():
    client, orchestrator = create_test_app()

    payload = {"session_id": "s1", "text": "Plan something"}

    response = client.post("/propose", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "message": "Plan proposed",
        "state": WorkflowState.PROPOSED,
        "plan": {"foo": "bar"}
    }

    orchestrator.propose.assert_called_once_with("Plan something", "s1")


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
