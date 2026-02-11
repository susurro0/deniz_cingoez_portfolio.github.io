import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from finops_llm_router.api.routes.fin_obs_routes import FinObsRoutes


@pytest.fixture
def mock_orchestrator():
    orchestrator = MagicMock()
    orchestrator.handle = AsyncMock(return_value={"prompt": "hello", "response": "ok", "model_type": "test-model"})
    orchestrator.list_providers.return_value = ["aws", "azure", "gcp"]
    return orchestrator


@pytest.fixture
def test_app(mock_orchestrator):
    app = FastAPI()
    routes = FinObsRoutes(mock_orchestrator)
    app.include_router(routes.router)
    return app


def test_health_endpoint(test_app):
    client = TestClient(test_app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "finops-llm-router"
    }


def test_metrics_endpoint(test_app):
    client = TestClient(test_app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "requests_total": 0,
        "cost_estimate_usd": 0.0,
        "avg_latency_ms": 0
    }


def test_providers_endpoint(test_app, mock_orchestrator):
    client = TestClient(test_app)
    response = client.get("/v1/providers")

    assert response.status_code == 200
    assert response.json() == {
        "providers": ["aws", "azure", "gcp"]
    }
    mock_orchestrator.list_providers.assert_called_once()


def test_llm_request_calls_orchestrator(test_app, mock_orchestrator):
    client = TestClient(test_app)

    payload = {"prompt": "hello", "model_type": "abc123"}
    response = client.post("/v1/llm", json=payload)

    assert response.status_code == 200
    assert response.json() == {'model_type': 'test-model', 'prompt': 'hello', 'response': 'ok'}

    mock_orchestrator.handle.assert_awaited_once()
    args, _ = mock_orchestrator.handle.call_args
    assert args[0].prompt == "hello"
    assert args[0].model_type == "abc123"
