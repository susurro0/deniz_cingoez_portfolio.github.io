from __future__ import annotations
import asyncio

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
        if hasattr(plan, "model_dump"):
            return plan.model_dump()
        return plan.dict()

    # -------------------------------------------------
    # EXECUTE IMMEDIATELY (ASYNC BACKGROUND)
    # -------------------------------------------------

    async def process_requestasync(self, user_input: str, session_id: str, user_id: str = "anonymous",
                      role: str = None, department: str = None):
        sanitized_input = self.scrubber.scrub(user_input)

        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {
                "entrypoint": "process_request",
                "input": sanitized_input,
                "user_id": user_id,
            },
        )

        # Phase 1: Understanding
        intent: Intent = await self.classifier.classify(user_input)

        self.auditor.log(
            session_id,
            "INTENT_CLASSIFIED",
            {
                "input": sanitized_input,
                "intent_name": intent.name,
                "adapter": intent.adapter,
                "method": intent.method,
                "entities": self.scrubber.scrub_data(intent.entities),
                "user_id": user_id,
            },
        )

        # Phase 2: Reasoning
        context = await self.state_store.get_context(session_id)
        if asyncio.iscoroutine(context):
            context = await context

        user_context = {
            "user_id": user_id,
            "role": role or context.get("role", "Employee"),
            "department": department or context.get("department", "Engineering"),
            **context.get("user_context", {}),
        }
        plan = await self.planner.generate_plan(intent, context)
        self.auditor.log_plan(session_id, plan)

        # Phase 3: Policy Validation
        if not await self.policy_engine.validate_plan(plan, user_context):
            return "Plan violates policy. Cannot execute."

        # Phase 4: Fire-and-forget execution
        asyncio.create_task(self.executor.run(plan, session_id=session_id))

        return "Execution started in background"

    # -------------------------------------------------
    # HUMAN-IN-THE-LOOP (PROPOSE / CONFIRM)
    # -------------------------------------------------

    async def propose(self, user_input: str, session_id: str, user_id: str = "anonymous",
                      role: str = None, department: str = None):
        sanitized_input = self.scrubber.scrub(user_input)

        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {"entrypoint": "propose", "input": sanitized_input, "user_id": user_id},
        )

        intent = await self.classifier.classify(user_input)


        self.auditor.log(
            session_id,
            "INTENT_CLASSIFIED",
            {
                "input": sanitized_input,
                "intent_name": intent.name,
                "adapter": intent.adapter,
                "method": intent.method,
                "entities": self.scrubber.scrub_data(intent.entities),
                "user_id": user_id,
            },
        )

        context = await self.state_store.get_context(session_id)
        if asyncio.iscoroutine(context):
            context = await context
        user_context = {
            "user_id": user_id,
            "role": role or context.get("role", "Employee"),
            "department": department or context.get("department", "Engineering"),
            **context.get("user_context", {}),
        }
        plan = await self.planner.generate_plan(intent, context.get("data", {}))
        self.auditor.log_plan(session_id, plan)

        if not await self.policy_engine.validate_plan(plan, user_context):
            return {
                "state": WorkflowState.REJECTED,
                "message": "Plan violates policy",
                "plan": None
            }


        plan_data = self._get_serialized_plan(plan)
        await self.state_store.save_context(
            session_id,
            {"last_plan": plan_data},
            state=WorkflowState.PROPOSED,
        )

        return {
            "state": WorkflowState.PROPOSED,
            "message": "Plan proposed, awaiting confirmation",
            "plan": plan_data,
        }

    async def confirm(self, session_id: str):
        self.auditor.log(session_id, "REQUEST_RECEIVED", {"entrypoint": "confirm"})

        context = await self.state_store.get_context(session_id)
        if asyncio.iscoroutine(context):
            context = await context

        if context.get("state") != WorkflowState.PROPOSED:
            return {"state": context.get("state"), "message": "Nothing to confirm"}

        plan_data = context["data"]["last_plan"]
        plan = Plan(**plan_data)

        asyncio.create_task(self.executor.run(plan, session_id=session_id))

        return {
            "state": WorkflowState.PROPOSED,
            "message": "Execution started in background",
        }

    async def reject(self, session_id: str):
        self.auditor.log(session_id, "REQUEST_RECEIVED", {"entrypoint": "reject"})

        context = await self.state_store.get_context(session_id)
        if asyncio.iscoroutine(context):
            context = await context

        if context.get("state") != WorkflowState.PROPOSED:
            return {"state": context.get("state"), "message": "Nothing to reject"}

        plan_data = context["data"]["last_plan"]
        await self.state_store.save_context(
            session_id,
            {"last_plan": plan_data},
            state=WorkflowState.REJECTED,
        )

        return {
            "state": WorkflowState.REJECTED,
            "message": "Plan rejected by user",
        }
