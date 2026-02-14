import pytest
from finops_llm_router.orchestrator.cost_first_strategy import CostFirstStrategy
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

def test_cost_first_strategy_selects_correct_models():
    strategy = CostFirstStrategy()

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )

    openai = DummyProvider("openai")
    anthropic = DummyProvider("anthropic")
    bedrock = DummyProvider("bedrock")
    other = DummyProvider("unknown")

    assert strategy.select_model(req, openai) == "GPT-4o-mini"
    assert strategy.select_model(req, anthropic) == "Claude-Haiku"
    assert strategy.select_model(req, bedrock) == "default-model"
    assert strategy.select_model(req, other) == "default-model"


# ----------------------------------------------------------------------
# 2. Test provider ranking order
# ----------------------------------------------------------------------

def test_cost_first_strategy_ranks_providers_correctly():
    strategy = CostFirstStrategy()

    providers = {
        "openai": DummyProvider("openai"),
        "anthropic": DummyProvider("anthropic"),
        "bedrock": DummyProvider("bedrock"),
    }

    req = FinObsRequest(
        id="req-2",
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )

    ranked = strategy.rank_providers(req, providers)

    # Expected order: openai → anthropic → bedrock
    assert ranked[0].name == "openai"
    assert ranked[1].name == "anthropic"
    assert ranked[2].name == "bedrock"


# ----------------------------------------------------------------------
# 3. Test ranking when some providers are missing
# ----------------------------------------------------------------------

def test_cost_first_strategy_handles_missing_providers():
    strategy = CostFirstStrategy()

    providers = {
        "openai": DummyProvider("openai")
        # anthropic and bedrock missing
    }

    req = FinObsRequest(
        id="req-3",
        prompt="hello",
        task_type="general",
        priority="cost",
        metadata={}
    )

    ranked = strategy.rank_providers(req, providers)
    assert strategy.name == 'cost-first'
    # Missing providers become None
    assert ranked == [
        providers["openai"],  # always first
        None,  # anthropic missing
        None  # bedrock missing
    ]
