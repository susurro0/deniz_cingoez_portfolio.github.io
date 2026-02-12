class Guardrails:
    """
    Checks prompts for PII, forbidden keywords, or cost violations.
    """

    forbidden_keywords = ["SSN", "credit card"]

    def validate(self, prompt: str) -> bool:
        return not any(word in prompt for word in self.forbidden_keywords)
