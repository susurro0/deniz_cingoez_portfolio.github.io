# src/finops_llm_router/providers/openai_provider.py
from .base_provider import BaseProvider
from typing import Any, Dict

from ..models.llm_result import LLMResult


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize client here (mock for POC)

    async def send_request(self, prompt: str, **kwargs) -> LLMResult:
        # Mocking the response for now

        return LLMResult(
            content=prompt,
            usage={
                "input_tokens": 42,
                "output_tokens": 30
            },
            cost_estimated=0.003,
        )

    async def health_check(self) -> bool:
        # Mocked health check
        return True

    async def get_usage(self, request_id: str) -> Dict[str, Any]:
        # Mocked usage stats
        return {
            "tokens_used": 42,
            "cost_estimate": 0.003
        }
