# src/finops_llm_router/orchestrator/performance_first_strategy.py
from .strategy import RoutingStrategy

class PerformanceFirstStrategy(RoutingStrategy):
    def select_provider(self, req, providers):
        return providers["openai"], "GPT-4"