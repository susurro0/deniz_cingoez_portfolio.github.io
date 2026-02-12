import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from finops_llm_router.api.app_factory import AppFactory


@pytest.fixture
def mock_orchestrator():
    """Mock FinObsLLMOrchestrator instance."""
    return MagicMock()


@pytest.fixture
def mock_routes():
    """Mock FinObsRoutes so we don't depend on real route logic."""
    mock = MagicMock()
    mock.router = MagicMock()
    return mock


@pytest.fixture
def app_factory(mock_orchestrator, mock_routes):
    """
    Patch orchestrator + routes so AppFactory can be tested in isolation.
    """
    with patch(
        "finops_llm_router.api.app_factory.FinObsLLMOrchestrator",
        return_value=mock_orchestrator
    ), patch(
        "finops_llm_router.api.app_factory.FinObsRoutes",
        return_value=mock_routes
    ):
        yield AppFactory()


def test_app_factory_creates_fastapi_app(app_factory):
    """AppFactory.get_app returns a FastAPI instance."""
    app = app_factory.get_app()
    assert app.title == "FinOps LLM Router POC"
    assert callable(app_factory.lifespan)


def test_lifespan_initializes_orchestrator(app_factory, mock_orchestrator):
    """
    Entering the lifespan context should create the orchestrator
    and register routes.
    """
    app = app_factory.get_app()

    # Trigger lifespan startup
    with TestClient(app) as client:
        assert app_factory.orchestrator is mock_orchestrator


def test_routes_are_registered(app_factory, mock_routes):
    """
    Ensure include_router is called with the FinObsRoutes.router.
    """
    app = app_factory.get_app()

    with patch.object(app, "include_router") as include_router:
        with TestClient(app):
            include_router.assert_called_once_with(mock_routes.router)


def test_app_factory_register_routes_direct_call(app_factory, mock_routes):
    """
    Directly calling _register_routes should include the router.
    """
    app = app_factory.get_app()

    with patch.object(app, "include_router") as include_router:
        app_factory._register_routes()
        include_router.assert_called_once_with(mock_routes.router)
