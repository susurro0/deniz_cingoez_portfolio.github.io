import re
from automation_app.models.intent import Intent


class IntentClassifier:
    """
    Deterministic, rule-based intent classifier.
    LLM-ready but not LLM-dependent.
    """

    async def classify(self, text: str) -> Intent:
        text_lower = text.lower()

        # ---- PTO / Workday ----
        if re.search(r"\b(pto|time off|vacation)\b", text_lower):
            return Intent(
                name="REQUEST_TIME_OFF",
                adapter="Workday",
                method="create_time_off",
                entities=self._extract_dates(text_lower),
            )

        # ---- Email / MSGraph ----
        if re.search(r"\b(send|email|mail)\b", text_lower):
            return Intent(
                name="SEND_EMAIL",
                adapter="MSGraph",
                method="send_email",
                entities=self._extract_email_entities(text_lower),
            )

        # ---- Calendar / MSGraph ----
        if re.search(r"\b(meeting|calendar|schedule)\b", text_lower):
            return Intent(
                name="CREATE_CALENDAR_EVENT",
                adapter="MSGraph",
                method="create_calendar_event",
                entities=self._extract_calendar_entities(text_lower),
            )

        raise ValueError("Unknown intent")

    # -------------------------------------------------
    # Entity extraction helpers (cheap but useful)
    # -------------------------------------------------

    def _extract_dates(self, text: str) -> dict:
        # Stub for now — future NLP or LLM
        return {}

    def _extract_email_entities(self, text: str) -> dict:
        return {}

    def _extract_calendar_entities(self, text: str) -> dict:
        return {}
