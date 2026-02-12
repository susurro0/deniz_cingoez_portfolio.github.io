import asyncio
import pytest

from finops_llm_router.providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_send_request_returns_expected_string():
    provider = OpenAIProvider()

    result = await provider.send_request("hello", "gpt-4")

    assert result == "[gpt-4] processed: hello"


@pytest.mark.asyncio
async def test_openai_provider_sleep_occurs(monkeypatch):
    """
    Ensures the provider awaits asyncio.sleep without actually waiting.
    """

    sleep_called = False

    async def fake_sleep(duration):
        nonlocal sleep_called
        sleep_called = True

    monkeypatch.setattr("asyncio.sleep", fake_sleep)

    provider = OpenAIProvider()
    result = await provider.send_request("test", "gpt-4")

    assert sleep_called is True
    assert result == "[gpt-4] processed: test"


def test_openai_provider_is_subclass_of_base_provider():
    from finops_llm_router.providers.base_provider import BaseProvider

    assert issubclass(OpenAIProvider, BaseProvider)
