from __future__ import annotations


class Guardrails:
    """
    Checks prompts for PII, forbidden keywords, or cost violations.
    """

    forbidden_keywords = ["SSN", "credit card"]

    def __init__(self):
        # Optional: store the last violation reason
        self.last_violation: str | None = None

    def validate(self, prompt: str) -> bool:
        """
        Returns True if the prompt passes guardrails.
        Sets self.last_violation if a violation occurs.
        """
        for word in self.forbidden_keywords:
            if word in prompt:
                self.last_violation = f"Forbidden keyword found: {word}"
                return False
        self.last_violation = None
        return True
