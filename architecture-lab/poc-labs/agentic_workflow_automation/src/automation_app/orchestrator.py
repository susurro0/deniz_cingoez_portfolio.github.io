from __future__ import annotations
import asyncio
from typing import Any, Dict

from automation_app.audit.audit_logger import AuditLogger
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan
from automation_app.models.workflow_state import WorkflowState
from automation_app.utils.pii_scrubber import PIIScrubber

class AgenticOrchestrator:
    def __init__(
        self,
        classifier=None,
        planner=None,
        policy_engine=None,
        executor=None,
        state_store=None,
        auditor=AuditLogger,
        scrubber=None,
    ):
        self.classifier = classifier
        self.planner = planner
        self.policy_engine = policy_engine
        self.executor = executor
        self.state_store = state_store
        self.auditor = auditor
        self.scrubber = scrubber or PIIScrubber()

    def _get_serialized_plan(self, plan: Plan) -> dict:
        """Helper to handle Pydantic v1 (dict) and v2 (model_dump) compatibility."""
        if hasattr(plan, "model_dump"):
            return plan.model_dump()
        return plan.dict()

    async def process_request(self, user_input: str, session_id: str, user_id: str = "anonymous"):
        # Scrubbing is usually CPU-bound and fast, but if it hits a DB/API, await it.
        sanitized_input = self.scrubber.scrub(user_input)

        # Assuming Auditor.log is now an async method
        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {
                "entrypoint": "process_request",
                "input": sanitized_input,
                "user_id": user_id
            },
        )

        # Phase 1: Understanding
        intent: Intent = await self.classifier.classify(user_input)
        self.auditor.log(
            session_id,
            "INTENT_CLASSIFIED",
            {
                "input": sanitized_input,
                "intent_type": intent.type,
                "intent_entity": intent.entity,
                "user_id": user_id
            },
        )

        # Phase 2: Reasoning
        context = await self.state_store.get_context(session_id)
        plan = await self.planner.generate_plan(intent, context)
        self.auditor.log_plan(session_id, plan)

        # Phase 3: Validation
        if not await self.policy_engine.validate_plan(plan):
            return "Plan violates policy. Cannot execute."

        # Phase 4: Async Execution (non-blocking)
        # We still use create_task, but the run method itself is awaited inside the task
        asyncio.create_task(self.executor.run(plan, session_id=session_id))

        return "Execution started in background"

    async def propose(self, user_input: str, session_id: str):
        sanitized_input = self.scrubber.scrub(user_input)
        self.auditor.log(session_id, "REQUEST_RECEIVED", {"entrypoint": "propose", "input": sanitized_input})

        intent = await self.classifier.classify(user_input)
        self.auditor.log(
            session_id,
            "INTENT_CLASSIFIED",
            {
                "input": sanitized_input,
                "intent_type": intent.type,
                "intent_entity": intent.entity,
            },
        )

        context = await self.state_store.get_context(session_id)
        plan = await self.planner.generate_plan(intent, context.get("data", {}))
        self.auditor.log_plan(session_id, plan)

        if not await self.policy_engine.validate_plan(plan):
            return {"state": WorkflowState.REJECTED, "message": "Plan violates policy", "plan": None}

        plan_data = self._get_serialized_plan(plan)
        await self.state_store.save_context(session_id, {"last_plan": plan_data}, state=WorkflowState.PROPOSED)

        return {"state": WorkflowState.PROPOSED, "message": "Plan proposed, awaiting confirmation", "plan": plan_data}

    async def confirm(self, session_id: str):
        self.auditor.log(session_id, "REQUEST_RECEIVED", {"entrypoint": "confirm"})

        context = await self.state_store.get_context(session_id)
        current_state = context.get("state")
        if current_state != WorkflowState.PROPOSED:
            return {"state": current_state, "message": "Nothing to confirm"}

        plan_data = context["data"]["last_plan"]
        plan = Plan(**plan_data)

        # Fire and forget
        asyncio.create_task(self.executor.run(plan, session_id=session_id))

        return {"state": WorkflowState.PROPOSED, "message": "Execution started in background"}

    async def reject(self, session_id: str):
        self.auditor.log(session_id, "REQUEST_RECEIVED", {"entrypoint": "reject"})

        context = await self.state_store.get_context(session_id)
        if context.get("state") != WorkflowState.PROPOSED:
            return {"state": context.get("state"), "message": "Nothing to reject"}

        plan_data = context["data"]["last_plan"]
        await self.state_store.save_context(session_id, {"last_plan": plan_data}, state=WorkflowState.REJECTED)

        return {"state": WorkflowState.REJECTED, "message": "Plan rejected by user"}