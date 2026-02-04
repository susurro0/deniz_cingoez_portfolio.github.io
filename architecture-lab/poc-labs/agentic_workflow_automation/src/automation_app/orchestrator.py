from automation_app.models.plan import Plan
from automation_app.models.workflow_state import WorkflowState


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


    def propose(self, user_input: str, session_id: str):
        intent = self.classifier.classify(user_input)
        context = self.state_store.get_context(session_id)
        plan = self.planner.generate_plan(intent, context.get("data", {}))

        # Validate plan but do NOT execute
        if not self.policy_engine.validate_plan(plan):
            return {
                "state": WorkflowState.REJECTED,
                "message": "Plan violates policy",
                "plan": None
            }

        # Save as PROPOSED
        self.state_store.save_context(session_id, {"last_plan": plan.dict()}, state=WorkflowState.PROPOSED)

        return {
            "state": WorkflowState.PROPOSED,
            "message": "Plan proposed, awaiting confirmation",
            "plan": plan.dict()
        }

    def confirm(self, session_id: str):
        context = self.state_store.get_context(session_id)
        if context["state"] != WorkflowState.PROPOSED:
            return {
                "state": context["state"],
                "message": "Nothing to confirm",
            }

        plan_data = context["data"]["last_plan"]
        # Convert dict back to Plan if needed
        plan = Plan(**plan_data)

        # Execute plan
        success = self.executor.run(plan)

        # Update state
        self.state_store.save_context(session_id, {"last_plan": plan_data}, state=WorkflowState.COMPLETED if success else WorkflowState.REJECTED)

        return {
            "state": WorkflowState.COMPLETED if success else WorkflowState.REJECTED,
            "message": "Execution completed" if success else "Execution failed"
        }

    def reject(self, session_id: str):
        context = self.state_store.get_context(session_id)
        if context["state"] != WorkflowState.PROPOSED:
            return {
                "state": context["state"],
                "message": "Nothing to reject"
            }

        plan_data = context["data"]["last_plan"]

        # Update state to REJECTED
        self.state_store.save_context(session_id, {"last_plan": plan_data}, state=WorkflowState.REJECTED)

        return {
            "state": WorkflowState.REJECTED,
            "message": "Plan rejected by user"
        }