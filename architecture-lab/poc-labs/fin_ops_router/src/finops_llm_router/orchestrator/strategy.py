# src/finops_llm_router/orchestrator/strategy.py
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List

from finops_llm_router.models.fin_obs_request import FinObsRequest
from finops_llm_router.providers.base_provider import BaseProvider

class RoutingStrategy(ABC):
    """Defines how a provider + model are selected."""

    @abstractmethod
    def select_model(self, req: FinObsRequest, provider: BaseProvider) -> str:
        """Return model name for this provider and request"""
        pass

    @abstractmethod
    def rank_providers(self, req: FinObsRequest, providers: Dict[str, BaseProvider]) -> List[BaseProvider]:
        """Return ordered list of providers for failover"""
        pass