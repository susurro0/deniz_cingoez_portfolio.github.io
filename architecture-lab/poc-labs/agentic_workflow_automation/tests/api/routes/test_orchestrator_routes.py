# tests/api/test_orchestrator_routes.py

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from automation_app.api.routes.orchestrator_routes import OrchestratorRoutes


def create_test_app():
    orchestrator = MagicMock()
    orchestrator.process_request.return_value = "Processed successfully"

    routes = OrchestratorRoutes(orchestrator)

    app = FastAPI()
    app.include_router(routes.router)

    client = TestClient(app)
    return client, orchestrator


def test_process_route_success():
    client, orchestrator = create_test_app()

    payload = {
        "session_id": "session-1",
        "text": "Hello orchestrator"
    }

    response = client.post("/process", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Processed successfully"}

    orchestrator.process_request.assert_called_once_with(
        user_input="Hello orchestrator",
        session_id="session-1"
    )


def test_process_route_validation_error():
    client, _ = create_test_app()

    response = client.post("/process", json={"session_id": "session-1"})

    assert response.status_code == 422


def test_process_route_passes_correct_types():
    client, orchestrator = create_test_app()

    payload = {
        "session_id": "abc123",
        "text": "Run something"
    }

    client.post("/process", json=payload)

    args, kwargs = orchestrator.process_request.call_args

    assert kwargs["session_id"] == "abc123"
    assert kwargs["user_input"] == "Run something"
