from smtpd import usage

import pytest
import asyncio
from unittest.mock import MagicMock

from finops_llm_router.providers.base_provider import BaseProvider
from finops_llm_router.models.llm_result import LLMResult


def test_base_provider_is_abstract():
    with pytest.raises(TypeError):
        BaseProvider()  # cannot instantiate abstract class


def test_missing_send_request_method():
    class BadProvider(BaseProvider):
        async def health_check(self):
            return True

        async def get_usage(self, request_id: str):
            return {}

    with pytest.raises(TypeError):
        BadProvider()


def test_missing_health_check_method():
    class BadProvider(BaseProvider):
        async def send_request(self, prompt: str, model: str):
            return LLMResult(content="x", usage={}, cost_estimated=0.0)

        async def get_usage(self, request_id: str):
            return {}

    with pytest.raises(TypeError):
        BadProvider()


def test_missing_get_usage_method():
    class BadProvider(BaseProvider):
        async def send_request(self, prompt: str, model: str):
            return LLMResult(content="x", usage={}, cost_estimated=0.0)

        async def health_check(self):
            return True

    with pytest.raises(TypeError):
        BadProvider()


@pytest.mark.asyncio
async def test_valid_provider_implementation():
    class GoodProvider(BaseProvider):
        name = "good"

        async def send_request(self, prompt: str, model: str):
            return LLMResult(
                content=f"{model}:{prompt}",
                usage={"input_tokens": 5, "output_tokens": 3},
                cost_estimated=0.001,
            )

        async def health_check(self):
            return True

        async def get_usage(self, request_id: str):
            return {"input_tokens": 5, "output_tokens": 3}

    provider = GoodProvider()

    # send_request
    result = await provider.send_request("hello", "gpt-4")
    assert isinstance(result, LLMResult)
    assert result.content == "gpt-4:hello"
    assert result.usage == {"input_tokens": 5, "output_tokens": 3}
    assert result.cost_estimated == 0.001

    # health_check
    assert await provider.health_check() is True

    # get_usage
    usage = await provider.get_usage("req-1")
    assert usage == {"input_tokens": 5, "output_tokens": 3}

class DummyProvider(BaseProvider):
    name = "dummy"

    async def send_request(self, prompt: str, model: str) -> LLMResult:
        return LLMResult(content="ok",
                         usage={
                            "input_tokens": 15,
                            "input_tokens": 45},
                         cost_estimated=0.01
                         )
    async def health_check(self) -> bool:
        return True

    async def get_usage(self, request_id: str):
        return {"usage": 1}

@pytest.mark.asyncio
async def test_dummy_provider_methods():
    provider = DummyProvider()
    res = await provider.send_request("hi", "model-x")
    assert res.content == "ok"
    assert await provider.health_check() is True
    assert await provider.get_usage("abc") == {"usage": 1}

@pytest.mark.asyncio
async def test_base_class_pass_coverage():
    """
    Call the abstract methods via a minimal subclass to hit `pass` lines.
    Ensures coverage for all abstract method lines in BaseProvider.
    """

    class MinimalProvider(BaseProvider):
        name = "minimal"

        async def send_request(self, prompt: str, model: str) -> LLMResult:
            return await super().send_request(prompt, model)

        async def health_check(self) -> bool:
            return await super().health_check()

        async def get_usage(self, request_id: str):
            return await super().get_usage(request_id)

    provider = MinimalProvider.__new__(MinimalProvider)

    # calling abstract methods triggers 'pass', no error
    await MinimalProvider.send_request(provider, "hi", "model-x")
    await MinimalProvider.health_check(provider)
    await MinimalProvider.get_usage(provider, "req-1")