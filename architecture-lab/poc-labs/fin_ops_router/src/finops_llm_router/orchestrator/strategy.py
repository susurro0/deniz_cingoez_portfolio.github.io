# src/finops_llm_router/orchestrator/strategy.py
from abc import ABC, abstractmethod
from typing import Dict, Tuple

from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.providers.base_provider import BaseProvider

class RoutingStrategy(ABC):
    """Defines how a provider is selected."""

    @abstractmethod
    def select(
            self,
            req: FinObsRequest,
            providers: Dict[str, BaseProvider],
    ) -> Tuple[BaseProvider, str]:
        pass
