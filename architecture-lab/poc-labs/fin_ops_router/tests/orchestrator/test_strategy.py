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
        def select(self, req, providers):
            return providers["dummy"], "gpt-4"

    strategy = GoodStrategy()

    req = FinObsRequest(
        id="req-1",
        prompt="hello",
        task_type="summarization",
        priority="cost",
        metadata={},
        model_type="dummy"
    )

    selected_provider, model_name = strategy.select(req, providers)

    assert selected_provider is provider
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
        def select(self, req, providers):
            # This will execute the `pass` in RoutingStrategy.select
            return super().select(req, providers)

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
    result = MinimalStrategy.select(strategy, req, providers)

    # `pass` returns None, so we just assert that we reached this point
    assert result is None
