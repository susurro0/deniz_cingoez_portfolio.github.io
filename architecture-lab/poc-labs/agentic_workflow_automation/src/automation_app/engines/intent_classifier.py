from automation_app.models.intent import Intent


class IntentClassifier:
    def classify(self, text: str) -> Intent:
        text_lower = text.lower()

        if "pto" in text_lower or "time off" in text_lower:
            return Intent(type="PTO", entity="date")

        raise ValueError("Unknown intent")
