import pytest

from finops_llm_router.orchestrator.performance_first_strategy import PerformanceFirstStrategy
from finops_llm_router.orchestrator.strategy import RoutingStrategy
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.providers.base_provider import BaseProvider


class DummyProvider(BaseProvider):
    name = "openai"

    async def send_request(self, prompt: str, model: str):
        return None

    async def health_check(self):
        return True

    async def get_usage(self, request_id: str):
        return {}


def test_performance_first_strategy_selects_openai_and_gpt4():
    strategy = PerformanceFirstStrategy()

    providers = {"openai": DummyProvider()}

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="performance",
        metadata={},
        model_type="openai",
    )

    provider, model_name = strategy.select(req, providers)

    assert provider is providers["openai"]
    assert model_name == "GPT-4"
    assert provider.name == "openai"
