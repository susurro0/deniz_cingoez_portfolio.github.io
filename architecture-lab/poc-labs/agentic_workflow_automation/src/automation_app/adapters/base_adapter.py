from abc import ABC, abstractmethod

class EnterpriseAdapter(ABC):

    @abstractmethod
    def execute(self, action: str, params: dict) -> dict:
        raise NotImplementedError("Subclasses must implement execute()")
