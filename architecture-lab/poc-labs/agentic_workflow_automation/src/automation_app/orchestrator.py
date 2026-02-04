

class AgenticOrchestrator:
    def __init__(self, classifier=None, planner=None, policy_engine=None, executor=None, state_store=None):
        self.classifier = classifier
        self.planner = planner
        self.policy_engine = policy_engine
        self.executor = executor
        self.state_store = state_store

    def process_request(self, user_input: str, session_id: str):
        # Phase 1: Understanding
        intent = self.classifier.classify(user_input)

        # Phase 2: Reasoning
        context = self.state_store.get_context(session_id)
        plan = self.planner.generate_plan(intent, context)

        # Phase 3: Validation
        if not self.policy_engine.validate_plan(plan):
            return "Plan violates policy. Cannot execute."

        # Phase 4: Execution
        success = self.executor.run(plan)

        # Phase 5: Persistence
        self.state_store.save_context(session_id, {"last_plan": plan.dict()})

        return "Execution completed" if success else "Execution failed"
