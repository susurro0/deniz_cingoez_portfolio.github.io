import asyncio

class BaseProvider:
    """
    Abstract base class for LLM providers.
    """

    async def send_request(self, prompt: str, model_name: str):
        raise NotImplementedError("Provider must implement send_request")

