from automation_app.models.workflow_state import WorkflowState


class StateStore:
    def __init__(self):
        self.storage = {}

    def save_context(self, session_id: str, data: dict, state: WorkflowState = WorkflowState.PROPOSED):
        self.storage[session_id] = {
            "state": state,
            "data": data
        }

    def get_context(self, session_id: str) -> dict:
        return self.storage.get(session_id, {
            "state": WorkflowState.PROPOSED,
            "data": {}
        })
