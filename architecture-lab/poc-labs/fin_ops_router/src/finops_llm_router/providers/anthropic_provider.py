# src/finops_llm_router/providers/anthropic_provider.py
from typing import Dict, Any
from .base_provider import BaseProvider
from ..models.llm_result import LLMResult

class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key  # just a placeholder for the POC

    async def send_request(self, prompt: str, **kwargs) -> LLMResult:
        # Mock response for POC
        return LLMResult(
            content=f"[Anthropic] {prompt}",
            usage={"input_tokens": 50, "output_tokens": 40},
            cost_estimated=0.005
        )

    async def health_check(self) -> bool:
        # Always healthy for POC; can toggle to simulate failover
        return True

    async def get_usage(self, request_id: str) -> Dict[str, Any]:
        # Mocked usage stats
        return {"tokens_used": 90, "cost_estimate": 0.005}
