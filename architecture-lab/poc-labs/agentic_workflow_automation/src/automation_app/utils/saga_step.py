from abc import ABC, abstractmethod

class SagaStep(ABC):
    @abstractmethod
    def execute(self, state):
        pass

    @abstractmethod
    def compensate(self, state):
        pass
