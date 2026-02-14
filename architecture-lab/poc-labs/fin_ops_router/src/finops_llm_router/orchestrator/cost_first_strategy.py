# src/finops_llm_router/orchestrator/cost_first_strategy.py
from typing import Dict, List

from .strategy import RoutingStrategy
from ..models.fin_obs_request import FinObsRequest
from ..providers.base_provider import BaseProvider


class CostFirstStrategy(RoutingStrategy):
    name = "cost-first"

    def rank_providers(self, req: FinObsRequest, providers: Dict[str, BaseProvider]) -> List[BaseProvider]:
        # Prefer cheaper providers first
        return [providers["openai"], providers.get("anthropic"), providers.get("bedrock")]

    def select_model(self, req: FinObsRequest, provider: BaseProvider) -> str:
        if provider.name == "openai":
            return "GPT-4o-mini"
        elif provider.name == "anthropic":
            return "Claude-Haiku"
        else:
            return "default-model"