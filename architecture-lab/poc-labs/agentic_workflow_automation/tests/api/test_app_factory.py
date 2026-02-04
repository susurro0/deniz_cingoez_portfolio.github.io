# tests/api/test_app_factory.py

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from automation_app.api.app_factory import AppFactory


def test_app_initializes():
    factory = AppFactory()
    app = factory.get_app()

    assert app is not None
    assert app.title == "Agentic Workflow Orchestrator"


def test_process_route_calls_orchestrator_correctly():
    # Patch the orchestrator inside AppFactory
    with patch(
        "automation_app.api.app_factory.AgenticOrchestrator"
    ) as MockOrchestrator:

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request.return_value = "OK"

        MockOrchestrator.return_value = mock_orchestrator

        factory = AppFactory()
        app = factory.get_app()
        client = TestClient(app)

        payload = {
            "session_id": "session-1",
            "text": "Book PTO for Friday"
        }

        response = client.post("/process", json=payload)

        assert response.status_code == 200
        assert response.json() == {"message": "OK",  'plan': None, 'state': None }

        mock_orchestrator.process_request.assert_called_once_with(
            user_input="Book PTO for Friday",
            session_id="session-1"
        )


def test_process_route_validation_error():
    factory = AppFactory()
    app = factory.get_app()
    client = TestClient(app)

    # Missing "text"
    response = client.post("/process", json={"session_id": "abc"})

    assert response.status_code == 422
