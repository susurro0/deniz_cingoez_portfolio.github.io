# src/finops_llm_router/providers/base_provider.py
from abc import ABC, abstractmethod
from typing import Any, Dict

from finops_llm_router.models.llm_result import LLMResult


class BaseProvider(ABC):
    """Abstract Base Class for all LLM Providers."""

    @abstractmethod
    async def send_request(self, prompt: str, model: str) -> LLMResult:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is available.
        Returns True if healthy, False otherwise.
        """
        pass

    @abstractmethod
    async def get_usage(self, request_id: str) -> Dict[str, Any]:
        """
        Return usage stats for a specific request if available.
        """
        pass
