# tests/api/test_app_factory.py

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock, ANY

from automation_app.api.app_factory import AppFactory


def test_app_initializes():
    factory = AppFactory()
    app = factory.get_app()

    assert app is not None
    assert app.title == "Agentic Workflow Orchestrator"


def test_process_route_calls_orchestrator_correctly():
    with patch(
        "automation_app.api.app_factory.AgenticOrchestrator"
    ) as MockOrchestrator:

        mock_orchestrator = MagicMock()
        mock_orchestrator.process_request = AsyncMock(return_value="OK")
        MockOrchestrator.return_value = mock_orchestrator

        factory = AppFactory()
        app = factory.get_app()

        # IMPORTANT: context manager
        with TestClient(app) as client:
            payload = {
                "session_id": "session-1",
                "text": "Book PTO for Friday"
            }

            response = client.post("/process", json=payload)

        assert response.status_code == 200
        assert response.json() == {
            "message": "OK",
            "plan": None,
            "state": None,
        }

        mock_orchestrator.process_request.assert_awaited_once_with(
            user_input="Book PTO for Friday",
            session_id="session-1",
            user_id='anonymous'
        )

def test_process_route_validation_error():
    factory = AppFactory()
    app = factory.get_app()

    with TestClient(app) as client:
        # Missing "text"
        response = client.post("/process", json={"session_id": "abc"})

    assert response.status_code == 422
