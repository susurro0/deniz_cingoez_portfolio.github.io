import pytest
from unittest.mock import MagicMock, AsyncMock

from finops_llm_router.models.llm_result import LLMResult
from finops_llm_router.orchestrator.finobs_llm_orchestrator import FinObsLLMOrchestrator
from finops_llm_router.models.fin_obs_request import FinObsRequest


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def mock_guard():
    guard = MagicMock()
    guard.validate.return_value = True
    return guard


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.name = "openai"
    return provider


@pytest.fixture
def mock_telemetry():
    telemetry = MagicMock()
    telemetry.capture = AsyncMock()
    return telemetry


@pytest.fixture
def fake_llm_result():
    result = MagicMock()
    result.content = "response-content"
    result.usage = {"tokens": 10}
    result.cost_estimated = 0.001
    return result


# ----------------------------------------------------------------------
# 1. Guardrail failure
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_guardrail_failure(mock_provider, mock_telemetry):
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


# ----------------------------------------------------------------------
# 2. Unknown strategy
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_unknown_strategy(mock_guard, mock_provider, mock_telemetry):
    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={"openai": mock_provider},
        telemetry=mock_telemetry,
    )

    req = FinObsRequest(
        prompt="hello",
        task_type="general",
        priority="invalid",
        metadata={}
    )

    with pytest.raises(ValueError):
        await orch.handle(req)


# ----------------------------------------------------------------------
# 3. Cost request (your requested test)
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_cost_request(
    mock_guard,
    mock_provider,
    mock_telemetry,
):
    # Arrange
    fake_llm_result = LLMResult(
        content="response-content",
        usage={"input_tokens": 5, "output_tokens": 5},
        cost_estimated=0.001,
    )

    mock_provider.send_request = AsyncMock(return_value=fake_llm_result)

    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={"openai": mock_provider},
        telemetry=mock_telemetry,
    )

    # Override the cost strategy behavior
    cost_strategy = orch.strategies["cost"]
    cost_strategy.rank_providers = MagicMock(return_value=[mock_provider])
    cost_strategy.select_model = MagicMock(return_value="gpt-cost-mini")

    req = FinObsRequest(
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={},
    )

    # Act
    resp = await orch.handle(req)

    # Assert — guardrails
    mock_guard.validate.assert_called_once_with("hello")

    # Assert — strategy
    cost_strategy.rank_providers.assert_called_once_with(req, {"openai": mock_provider})
    cost_strategy.select_model.assert_called_once_with(req, mock_provider)

    # Assert — provider call
    mock_provider.send_request.assert_called_once_with(
        prompt="hello",
        model="gpt-cost-mini",
    )

    # Assert — telemetry
    mock_telemetry.capture.assert_called_once()
    telemetry_kwargs = mock_telemetry.capture.call_args.kwargs
    assert telemetry_kwargs["provider"] == "openai"
    assert telemetry_kwargs["model"] == "gpt-cost-mini"

    # Assert — response
    assert resp.content == "response-content"
    assert resp.model_used == "gpt-cost-mini"
    assert resp.provider == "openai"
    assert resp.usage == {"input_tokens": 5, "output_tokens": 5}
    assert resp.cost_estimated == 0.001
    assert isinstance(resp.latency_ms, float)

# ----------------------------------------------------------------------
# 4. Failover: first provider fails, second succeeds
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_failover_to_second_provider(mock_guard, mock_telemetry, fake_llm_result):
    p1 = AsyncMock()
    p1.name = "p1"
    p1.send_request.side_effect = Exception("boom")

    p2 = AsyncMock()
    p2.name = "p2"
    p2.send_request.return_value = fake_llm_result

    strategy = MagicMock()
    strategy.rank_providers.return_value = [p1, p2]
    strategy.select_model.return_value = "gpt-test"

    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={"p1": p1, "p2": p2},
        telemetry=mock_telemetry,
    )
    orch.strategies = {"cost": strategy}

    req = FinObsRequest(
        id="test-id",
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )

    resp = await orch.handle(req)

    assert resp.provider == "p2"
    assert p1.send_request.called
    assert p2.send_request.called


# ----------------------------------------------------------------------
# 5. All providers fail
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_all_providers_fail(mock_guard, mock_telemetry):
    p1 = MagicMock()
    p1.name = "p1"
    p1.send_request.side_effect = Exception("fail1")

    p2 = MagicMock()
    p2.name = "p2"
    p2.send_request.side_effect = Exception("fail2")

    strategy = MagicMock()
    strategy.rank_providers.return_value = [p1, p2]
    strategy.select_model.return_value = "gpt-test"

    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={"p1": p1, "p2": p2},
        telemetry=mock_telemetry,
    )
    orch.strategies = {"cost": strategy}

    req = FinObsRequest(
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )

    with pytest.raises(RuntimeError):
        await orch.handle(req)


# ----------------------------------------------------------------------
# 6. Telemetry is called
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_telemetry_called(mock_guard, mock_provider, mock_telemetry, fake_llm_result):
    mock_provider.send_request = AsyncMock(return_value=fake_llm_result)
    strategy = MagicMock()
    strategy.rank_providers.return_value = [mock_provider]
    strategy.select_model.return_value = "gpt-test"

    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={"openai": mock_provider},
        telemetry=mock_telemetry,
    )
    orch.strategies = {"cost": strategy}

    req = FinObsRequest(
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )

    await orch.handle(req)

    assert mock_telemetry.capture.called


# ----------------------------------------------------------------------
# 7. list_providers
# ----------------------------------------------------------------------

def test_list_providers(mock_guard, mock_telemetry):
    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={"a": MagicMock(), "b": MagicMock()},
        telemetry=mock_telemetry,
    )

    assert orch.list_providers() == ["a", "b"]

# ----------------------------------------------------------------------
# 8. No providers returned by strategy
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_handle_no_providers(mock_guard, mock_telemetry):
    orch = FinObsLLMOrchestrator(
        guardrails=mock_guard,
        providers={},  # no providers configured
        telemetry=mock_telemetry,
    )

    empty_strategy = MagicMock()
    empty_strategy.rank_providers.return_value = []
    orch.strategies = {"cost": empty_strategy}

    req = FinObsRequest(
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )
    with pytest.raises(RuntimeError) as exc:
        await orch.handle(req)

    assert "No providers available for routing." in str(exc.value)
