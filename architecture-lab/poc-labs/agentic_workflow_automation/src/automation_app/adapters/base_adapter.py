from abc import ABC, abstractmethod
from typing import Dict, Any, Set


class EnterpriseAdapter(ABC):

    @abstractmethod
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a side-effecting action against an enterprise system.
        Must return a dict containing any external IDs required for compensation.
        """
        raise NotImplementedError

    @abstractmethod
    def compensate(
        self,
        action: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
    ) -> None:
        """
        Reverses the effects of execute().
        Must be safe to call multiple times (idempotent).
        """
        raise NotImplementedError

    @abstractmethod
    def supported_actions(self) -> Set[str]:
        """
        Returns a set of all actions this adapter can handle.
        Used for validation before execution.
        """
        raise NotImplementedError