import pytest

from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.orchestrator.cost_first_strategy import CostFirstStrategy
from finops_llm_router.providers.base_provider import BaseProvider


class DummyProvider(BaseProvider):
    name = "openai"

    async def send_request(self, prompt: str, model: str):
        return None

    async def health_check(self):
        return True

    async def get_usage(self, request_id: str):
        return {}


def test_cost_first_strategy_selects_openai_and_gpt4():
    strategy = CostFirstStrategy()

    providers = {"openai": DummyProvider()}

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="cost",
        metadata={},
        model_type="openai",
    )

    provider, model_name = strategy.select(req, providers)

    assert provider is providers["openai"]
    assert model_name == "GPT-4o-mini"
    assert provider.name == "openai"
