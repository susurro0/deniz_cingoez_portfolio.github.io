import pytest
from unittest.mock import MagicMock, AsyncMock

from finops_llm_router.models.llm_result import LLMResult
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
    strategy.select = MagicMock()
    return strategy


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.name = "openai"
    provider.send_request = AsyncMock(
        return_value=LLMResult(
            content="processed text",
            usage={"input_tokens": 5, "output_tokens": 15},
            cost_estimated=0.002,
        )
    )
    provider.health_check = AsyncMock(return_value=True)
    return provider


@pytest.fixture
def mock_telemetry():
    tel = MagicMock()
    tel.capture = AsyncMock()
    return tel


@pytest.fixture
def orchestrator(mock_guardrails, mock_provider, mock_telemetry):
    providers = {"openai": mock_provider}
    return FinObsLLMOrchestrator(
        guardrails=mock_guardrails,
        providers=providers,
        telemetry=mock_telemetry,
    )

@pytest.fixture
def req():
    return FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="cost",
        metadata={},
        model_type="openai"
    )

@pytest.mark.asyncio
async def test_handle_guardrail_failure(mock_strategy, mock_provider, mock_telemetry):
    guard = MagicMock()
    guard.validate.return_value = False

    orch = FinObsLLMOrchestrator(
        guardrails=guard,
        providers={"openai": mock_provider},
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

@pytest.mark.asyncio
async def test_handle_cost_request(orchestrator, mock_provider, mock_telemetry):
    from finops_llm_router.models.fin_obs_request import FinObsRequest

    request = FinObsRequest(
        prompt="Hello world",
        task_type="general",
        priority="cost",
        metadata={"request_id": "test-1"},
    )

    response = await orchestrator.handle(request)

    assert response.content == "processed text"
    assert response.provider == "openai"
    assert response.usage["input_tokens"] == 5
    assert response.cost_estimated == 0.002

    mock_provider.send_request.assert_awaited_once()
    mock_telemetry.capture.assert_awaited_once()

@pytest.mark.asyncio
async def test_handle_unknown_strategy_raises(orchestrator):
    # Arrange: request with a priority that doesn't exist
    request = FinObsRequest(
        prompt="Some text",
        task_type="general",
        priority="nonexistent",  # This should trigger the error
        metadata={"request_id": "test-unknown"},
    )

    # Act & Assert: ensure ValueError is raised
    with pytest.raises(ValueError) as exc_info:
        await orchestrator.handle(request)

    assert "Unknown routing strategy" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_failover_when_primary_healthy(mock_strategy, mock_telemetry, req):
    # Primary provider
    primary = MagicMock()
    primary.name = "openai"
    primary.health_check = AsyncMock(return_value=True)
    primary.send_request = AsyncMock(
        return_value=LLMResult(
            content="ok",
            usage={"input_tokens": 1, "output_tokens": 1},
            cost_estimated=0.001,
        )
    )

    providers = {"openai": primary}

    orch = FinObsLLMOrchestrator(
        guardrails=MagicMock(validate=lambda _: True),
        providers=providers,
        telemetry=mock_telemetry,
    )

    mock_strategy.select.return_value = (primary, "GPT-4")

    result = await orch.handle(req)

    assert result.provider == "openai"
    primary.send_request.assert_awaited_once()
    primary.health_check.assert_awaited_once()

@pytest.mark.asyncio
async def test_failover_to_healthy_alternative(mock_strategy, mock_telemetry, req):
    primary = MagicMock()
    primary.name = "openai"
    primary.health_check = AsyncMock(return_value=False)

    healthy_alt = MagicMock()
    healthy_alt.name = "anthropic"
    healthy_alt.health_check = AsyncMock(return_value=True)
    healthy_alt.send_request = AsyncMock(
        return_value=LLMResult(
            content="alt-ok",
            usage={"input_tokens": 2, "output_tokens": 2},
            cost_estimated=0.002,
        )
    )

    providers = {"openai": primary, "anthropic": healthy_alt}

    orch = FinObsLLMOrchestrator(
        guardrails=MagicMock(validate=lambda _: True),
        providers=providers,
        telemetry=mock_telemetry,
    )

    mock_strategy.select.return_value = (primary, "GPT-4")

    result = await orch.handle(req)

    assert result.provider == "anthropic"
    healthy_alt.send_request.assert_awaited_once()
    primary.send_request.assert_not_called()

@pytest.mark.asyncio
async def test_failover_no_healthy_providers_raises(mock_strategy, mock_telemetry, req):
    primary = MagicMock()
    primary.name = "openai"
    primary.health_check = AsyncMock(return_value=False)

    alt = MagicMock()
    alt.name = "anthropic"
    alt.health_check = AsyncMock(return_value=False)

    providers = {"openai": primary, "anthropic": alt}

    orch = FinObsLLMOrchestrator(
        guardrails=MagicMock(validate=lambda _: True),
        providers=providers,
        telemetry=mock_telemetry,
    )

    mock_strategy.select.return_value = (primary, "GPT-4")

    with pytest.raises(RuntimeError, match="No healthy providers available"):
        await orch.handle(req)


