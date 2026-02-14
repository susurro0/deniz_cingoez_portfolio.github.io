import pytest

from finops_llm_router.providers.anthropic_provider import AnthropicProvider
from finops_llm_router.providers.openai_provider import OpenAIProvider
from finops_llm_router.models.llm_result import LLMResult


@pytest.mark.asyncio
async def test_send_request_returns_llmresult():
    provider = AnthropicProvider(api_key="dummy")

    result = await provider.send_request("hello world")

    assert isinstance(result, LLMResult)
    assert result.content == "[Anthropic] hello world"
    assert result.usage == {
        "input_tokens": 50,
        "output_tokens": 40,
    }
    assert result.cost_estimated == 0.005


@pytest.mark.asyncio
async def test_health_check_returns_true():
    provider = AnthropicProvider(api_key="dummy")

    healthy = await provider.health_check()

    assert healthy is True


@pytest.mark.asyncio
async def test_get_usage_returns_expected_dict():
    provider = AnthropicProvider(api_key="dummy")

    usage = await provider.get_usage("req-123")

    assert usage == {
        "tokens_used": 90,
        "cost_estimate": 0.005,
    }


def test_provider_has_correct_name():
    provider = AnthropicProvider(api_key="dummy")
    assert provider.name == "anthropic"
