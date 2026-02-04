class ExecutionEngine:
    def __init__(self, adapters: dict):
        self.adapters = adapters

    def run(self, plan):
        for action in plan.actions:
            adapter = self.adapters.get(action.adapter)
            if not adapter:
                raise ValueError(f"No adapter registered for {action.adapter}")

            adapter.execute(action.method, action.params)

        return True

    def rollback(self, step_id: str):
        # Stub
        pass
