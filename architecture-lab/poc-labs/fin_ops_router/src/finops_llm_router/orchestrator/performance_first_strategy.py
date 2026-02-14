# src/finops_llm_router/orchestrator/performance_first_strategy.py
from typing import Dict, List

from .strategy import RoutingStrategy
from ..models.fin_obs_request import FinObsRequest
from ..providers.base_provider import BaseProvider


class PerformanceFirstStrategy(RoutingStrategy):
    name = "performance-first"

    def rank_providers(self, req: FinObsRequest, providers: Dict[str, BaseProvider]) -> List[BaseProvider]:
        # Prefer high-performance providers first
        return [providers.get("anthropic"), providers.get("bedrock"), providers["openai"]]


    def select_model(self, req: FinObsRequest, provider: BaseProvider) -> str:
        if provider.name == "openai":
            return "GPT-4"
        elif provider.name == "anthropic":
            return "Claude-2"
        elif provider.name == "bedrock":
            return "Titan-1"
        else:
            return "default-model"