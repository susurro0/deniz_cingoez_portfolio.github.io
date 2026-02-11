import asyncio

from finops_llm_router.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    Dummy OpenAI provider for POC.
    """

    async def send_request(self, prompt: str, model_name: str):
        await asyncio.sleep(0.1)
        return f"[{model_name}] processed: {prompt}"
