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
def mock_telemetry():
    tel = MagicMock()
    tel.capture = AsyncMock()
    return tel


@pytest.fixture
def orchestrator(mock_guardrails, mock_telemetry):
    orch = FinObsLLMOrchestrator(
        guardrails=mock_guardrails,
        telemetry=mock_telemetry
    )
    orch.providers["openai"].send_request = AsyncMock(return_value="processed text")
    return orch


@pytest.mark.asyncio
async def test_handle_success_default_model(orchestrator, mock_telemetry):
    req = FinObsRequest(prompt="hello", model_type="openai")

    result = await orchestrator.handle(req)

    assert isinstance(result, FinObsResponse)
    assert result.prompt == "hello"
    assert result.response == "processed text"
    assert result.model_type == "GPT-4"

    orchestrator.providers["openai"].send_request.assert_awaited_once_with(
        "hello", "GPT-4"
    )
    mock_telemetry.capture.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_cost_model_uses_gpt4o_mini(orchestrator):
    req = FinObsRequest(prompt="hello", model_type="cost")

    result = await orchestrator.handle(req)

    assert result.model_type == "GPT-4o-mini"
    orchestrator.providers["openai"].send_request.assert_awaited_once_with(
        "hello", "GPT-4o-mini"
    )


@pytest.mark.asyncio
async def test_handle_guardrail_failure(mock_telemetry):
    guard = MagicMock()
    guard.validate.return_value = False

    orch = FinObsLLMOrchestrator(
        guardrails=guard,
        telemetry=mock_telemetry
    )

    req = FinObsRequest(prompt="bad", model_type="openai")

    with pytest.raises(ValueError):
        await orch.handle(req)


def test_list_providers(orchestrator):
    assert orchestrator.list_providers() == ["openai"]
