import pytest
from unittest.mock import MagicMock, AsyncMock

from finops_llm_router.orchestrator.finobs_llm_orchestrator import FinObsLLMOrchestrator
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.models.fin_obs_response import FinObsResponse


@pytest.fixture
def mock_guardrails():
    guard = MagicMock()
    guard.validate.return_value = True
    return guard


@pytest.fixture
def mock_strategy():
    strategy = MagicMock()
    # Will be overridden in individual tests
    strategy.select = MagicMock()
    return strategy


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.name = "openai"
    provider.send_request = AsyncMock(return_value="processed text")
    return provider


@pytest.fixture
def mock_telemetry():
    tel = MagicMock()
    tel.capture = AsyncMock()
    return tel


@pytest.fixture
def orchestrator(mock_guardrails, mock_provider, mock_strategy, mock_telemetry):
    providers = {"openai": mock_provider}
    return FinObsLLMOrchestrator(
        guardrails=mock_guardrails,
        providers=providers,
        strategy=mock_strategy,
        telemetry=mock_telemetry,
    )


@pytest.mark.asyncio
async def test_handle_success(orchestrator, mock_strategy, mock_provider, mock_telemetry):
    req = FinObsRequest(
        prompt="hello",
        task_type="summarization",
        priority="cost",
        metadata={}
    )

    # Strategy chooses provider + model
    mock_strategy.select.return_value = (mock_provider, "GPT-4")

    result = await orchestrator.handle(req)

    assert isinstance(result, FinObsResponse)
    assert result.prompt == "hello"
    assert result.response == "processed text"
    assert result.model_type == "GPT-4"

    mock_strategy.select.assert_called_once_with(req, orchestrator.providers)
    mock_provider.send_request.assert_awaited_once_with(prompt="hello", model="GPT-4")
    mock_telemetry.capture.assert_awaited_once_with(
        prompt="hello",
        response="processed text",
        model_used="GPT-4",
        provider="openai",
    )


@pytest.mark.asyncio
async def test_handle_guardrail_failure(mock_strategy, mock_provider, mock_telemetry):
    guard = MagicMock()
    guard.validate.return_value = False

    orch = FinObsLLMOrchestrator(
        guardrails=guard,
        providers={"openai": mock_provider},
        strategy=mock_strategy,
        telemetry=mock_telemetry,
    )

    req = FinObsRequest(
        prompt="blocked",
        task_type="general",
        priority="cost",
        metadata={}
    )

    with pytest.raises(ValueError):
        await orch.handle(req)

    guard.validate.assert_called_once_with("blocked")


def test_list_providers(orchestrator):
    assert orchestrator.list_providers() == ["openai"]
