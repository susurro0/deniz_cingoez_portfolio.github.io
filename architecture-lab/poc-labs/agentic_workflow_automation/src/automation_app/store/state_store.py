class StateStore:
    def __init__(self):
        self.storage = {}

    def save_context(self, session_id: str, data: dict):
        self.storage[session_id] = data

    def get_context(self, session_id: str) -> dict:
        return self.storage.get(session_id, {})
