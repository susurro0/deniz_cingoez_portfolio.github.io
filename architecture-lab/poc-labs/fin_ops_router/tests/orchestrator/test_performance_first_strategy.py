import pytest
from unittest.mock import MagicMock
from finops_llm_router.orchestrator.performance_first_strategy import PerformanceFirstStrategy
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.providers.base_provider import BaseProvider


class DummyProvider(BaseProvider):
    def __init__(self, name):
        self.name = name

    async def send_request(self, prompt: str, model: str):
        return None

    async def health_check(self):
        return True

    async def get_usage(self, request_id: str):
        return {}


# ----------------------------------------------------------------------
# 1. Test model selection for each provider
# ----------------------------------------------------------------------

def test_performance_first_strategy_selects_correct_models():
    strategy = PerformanceFirstStrategy()

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="performance",
        metadata={}
    )

    openai = DummyProvider("openai")
    anthropic = DummyProvider("anthropic")
    bedrock = DummyProvider("bedrock")
    other = DummyProvider("unknown")

    assert strategy.select_model(req, openai) == "GPT-4"
    assert strategy.select_model(req, anthropic) == "Claude-2"
    assert strategy.select_model(req, bedrock) == "Titan-1"
    assert strategy.select_model(req, other) == "default-model"


# ----------------------------------------------------------------------
# 2. Test provider ranking order
# ----------------------------------------------------------------------

def test_performance_first_strategy_ranks_providers_correctly():
    strategy = PerformanceFirstStrategy()

    providers = {
        "openai": DummyProvider("openai"),
        "anthropic": DummyProvider("anthropic"),
        "bedrock": DummyProvider("bedrock"),
    }

    req = FinObsRequest(
        id="req-2",
        prompt="hello",
        task_type="general",
        priority="performance",
        metadata={}
    )

    ranked = strategy.rank_providers(req, providers)

    # Expected order: anthropic → bedrock → openai
    assert ranked[0].name == "anthropic"
    assert ranked[1].name == "bedrock"
    assert ranked[2].name == "openai"


# ----------------------------------------------------------------------
# 3. Test ranking when some providers are missing
# ----------------------------------------------------------------------

def test_performance_first_strategy_handles_missing_providers():
    strategy = PerformanceFirstStrategy()

    # Only openai exists
    providers = {
        "openai": DummyProvider("openai")
    }

    req = FinObsRequest(
        id="req-3",
        prompt="hello",
        task_type="general",
        priority="performance",
        metadata={}
    )

    ranked = strategy.rank_providers(req, providers)

    # Missing providers become None, but openai is always last
    assert ranked == [None, None, providers["openai"]]
