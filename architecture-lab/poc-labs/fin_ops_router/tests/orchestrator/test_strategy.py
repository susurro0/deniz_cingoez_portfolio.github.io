import pytest
from unittest.mock import MagicMock

from finops_llm_router.orchestrator.strategy import RoutingStrategy
from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.providers.base_provider import BaseProvider


def test_routing_strategy_is_abstract():
    with pytest.raises(TypeError):
        RoutingStrategy()  # cannot instantiate abstract class


def test_missing_select_method():
    class BadStrategy(RoutingStrategy):
        pass

    with pytest.raises(TypeError):
        BadStrategy()


@pytest.mark.asyncio
async def test_valid_strategy_selects_provider_and_model():
    # Fake provider
    class DummyProvider(BaseProvider):
        name = "dummy"

        async def send_request(self, prompt: str, model: str):
            pass

        async def health_check(self):
            return True

        async def get_usage(self, request_id: str):
            return {}

    provider = DummyProvider()
    providers = {"dummy": provider}

    # Valid strategy implementation
    class GoodStrategy(RoutingStrategy):
        def select_model(self, req, provider):
            return "gpt-4"
        def rank_providers(self, req, providers):
            return [providers.get("dummy")]
    strategy = GoodStrategy()

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="cost",
        metadata={},
        model_type="dummy"
    )

    model_name = strategy.select_model(req, provider)

    assert model_name == "gpt-4"

class DummyProvider(BaseProvider):
    name = "dummy"

    async def send_request(self, prompt: str, model: str):
        return None

    async def health_check(self) -> bool:
        return True

    async def get_usage(self, request_id: str):
        return {}


def test_routing_strategy_pass_coverage():
    """
    Call the abstract `select` via a minimal subclass to hit the `pass` line.
    Ensures coverage for the abstract method body in RoutingStrategy.
    """

    class MinimalStrategy(RoutingStrategy):
        def select_model(self, req, provider):
            # This will execute the `pass` in RoutingStrategy.select
            return super().select_model(req, provider)
        def rank_providers(self, req, providers):
            return super().rank_providers(req, providers)
    # Bypass ABC __init__ by using __new__
    strategy = MinimalStrategy.__new__(MinimalStrategy)

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="cost",
        metadata={},
        model_type="dummy",
    )
    providers = {"dummy": DummyProvider()}

    # This will run the base class `select` body (which is just `pass`)
    select_model = MinimalStrategy.select_model(strategy, req, providers['dummy'])
    rank_providers = MinimalStrategy.rank_providers(strategy, req, providers)
    # `pass` returns None, so we just assert that we reached this point
    assert select_model is None
    assert rank_providers is None
