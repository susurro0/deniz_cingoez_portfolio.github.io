import pytest
import asyncio

from finops_llm_router.providers.base_provider import BaseProvider


def test_base_provider_send_request_raises_not_implemented():
    provider = BaseProvider()

    with pytest.raises(NotImplementedError):
        asyncio.run(provider.send_request("hello", "gpt-4"))


def test_subclass_must_override_send_request():
    class BadProvider(BaseProvider):
        pass

    provider = BadProvider()

    with pytest.raises(NotImplementedError):
        asyncio.run(provider.send_request("hello", "gpt-4"))


def test_subclass_implements_send_request_successfully():
    class GoodProvider(BaseProvider):
        async def send_request(self, prompt: str, model_name: str):
            return f"{model_name}: {prompt}"

    provider = GoodProvider()

    result = asyncio.run(provider.send_request("hello", "gpt-4"))
    assert result == "gpt-4: hello"
