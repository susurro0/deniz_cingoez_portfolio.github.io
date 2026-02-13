# src/finops_llm_router/orchestrator/cost_first_strategy.py
from .strategy import RoutingStrategy


class CostFirstStrategy(RoutingStrategy):
    def select(self, req, providers):
        return providers["openai"], "GPT-4o-mini"