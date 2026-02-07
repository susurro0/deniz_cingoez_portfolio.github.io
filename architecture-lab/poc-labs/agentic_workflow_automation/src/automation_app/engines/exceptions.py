# automation_app/engines/exceptions.py
from __future__ import annotations

from automation_app.config.constants import RecoveryDecision


class ActionFailure(Exception):
    """
    Raised when an action fails after retries
    and requires higher-level orchestration decisions.
    """

    def __init__(self, decision: RecoveryDecision | str , original: Exception):
        self.decision = decision
        self.original = original
        super().__init__(str(original))
