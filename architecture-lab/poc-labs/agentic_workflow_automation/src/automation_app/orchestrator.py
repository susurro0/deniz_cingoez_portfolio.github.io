from __future__ import annotations

import asyncio
import time
import uuid

from automation_app.audit.audit_logger import AuditLogger
from automation_app.config.constants import HITL_TIMEOUT_SECONDS
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
            return plan.model_dump(mode="json")
        return plan.dict()

    def _build_user_context(self, base_context: dict, user_id: str, role: str | None, department: str | None) -> dict:
        base_role = base_context.get("role", "Employee")
        base_department = base_context.get("department", "Engineering")
        user_ctx_extra = base_context.get("user_context", {}) or {}

        # Explicit args win over stored context; stored context fills gaps
        merged = {
            "user_id": user_id,
            "role": role or base_role,
            "department": department or base_department,
        }
        for k, v in user_ctx_extra.items():
            if k not in merged:
                merged[k] = v
        return merged

    async def _run_with_audit(self, plan: Plan, session_id: str):
        try:
            await self.executor.run(plan, session_id=session_id)
        except Exception as e:
            self.auditor.log(
                session_id,
                WorkflowState.REJECTED,
                {"error": str(e)},
            )

    async def _get_context(self, session_id: str) -> dict:
        context = await self.state_store.get_context(session_id)
        return context or {}

    # -------------------------------------------------
    # EXECUTE IMMEDIATELY (ASYNC BACKGROUND)
    # -------------------------------------------------

    async def process_requestasync(
        self,
        user_input: str,
        session_id: str,
        user_id: str = "anonymous",
        role: str | None = None,
        department: str | None = None,
    ):
        request_id = str(uuid.uuid4())
        sanitized_input = self.scrubber.scrub(user_input)

        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {
                "entrypoint": "process_request",
                "input": sanitized_input,
                "user_id": user_id,
                "request_id": request_id,
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
                "request_id": request_id,
            },
        )

        # Phase 2: Reasoning
        context = await self._get_context(session_id)
        user_context = self._build_user_context(context, user_id, role, department)

        plan = await self.planner.generate_plan(intent, context)
        self.auditor.log_plan(session_id, plan)

        # Phase 3: Policy Validation
        if not await self.policy_engine.validate_plan(plan, user_context):
            return "Plan violates policy. Cannot execute."

        # Phase 4: Fire-and-forget execution
        asyncio.create_task(self._run_with_audit(plan, session_id=session_id))

        return "Execution started in background"

    # -------------------------------------------------
    # HUMAN-IN-THE-LOOP (PROPOSE / CONFIRM)
    # -------------------------------------------------

    async def propose(
        self,
        user_input: str,
        session_id: str,
        user_id: str = "anonymous",
        role: str | None = None,
        department: str | None = None,
    ):
        request_id = str(uuid.uuid4())
        sanitized_input = self.scrubber.scrub(user_input)

        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {
                "entrypoint": "propose",
                "input": sanitized_input,
                "user_id": user_id,
                "request_id": request_id,
            },
        )

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
                "request_id": request_id,
            },
        )

        context = await self._get_context(session_id)
        user_context = self._build_user_context(context, user_id, role, department)

        # Keep existing behavior: planner gets context["data"] if present
        plan_context = context.get("data", {})
        plan = await self.planner.generate_plan(intent, plan_context)
        self.auditor.log_plan(session_id, plan)

        if not await self.policy_engine.validate_plan(plan, user_context):
            return {
                "state": WorkflowState.REJECTED,
                "message": "Plan violates policy",
                "plan": None,
            }

        plan_data = self._get_serialized_plan(plan)
        timestamp = time.time()

        await self.state_store.save_context(
            session_id,
            {"last_plan": plan_data},
            state=WorkflowState.PROPOSED,
            timestamp=timestamp,
        )

        return {
            "state": WorkflowState.PROPOSED,
            "message": "Plan proposed, awaiting confirmation",
            "plan": plan_data,
        }

    async def confirm(self, session_id: str):
        request_id = str(uuid.uuid4())
        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {"entrypoint": "confirm", "request_id": request_id},
        )

        context = await self._get_context(session_id)

        if context.get("state") != WorkflowState.PROPOSED:
            return {"state": context.get("state"), "message": "Nothing to confirm"}

        plan_data = context["data"]["last_plan"]
        plan = Plan(**plan_data)

        # Update state to reflect that execution has started
        await self.state_store.save_context(
            session_id,
            {"last_plan": plan_data},
            state=WorkflowState.IN_PROGRESS,
        )

        asyncio.create_task(self._run_with_audit(plan, session_id=session_id))

        return {
            "state": WorkflowState.IN_PROGRESS,
            "message": "Execution started in background",
        }

    async def reject(self, session_id: str):
        request_id = str(uuid.uuid4())
        self.auditor.log(
            session_id,
            "REQUEST_RECEIVED",
            {"entrypoint": "reject", "request_id": request_id},
        )

        context = await self._get_context(session_id)

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

    async def cleanup_stale_proposals(self, timeout_seconds: int = HITL_TIMEOUT_SECONDS):
        """
        Auto-reject proposals that have been in PROPOSED state longer than timeout.
        """
        sessions = await self.state_store.get_all_sessions()
        now = time.time()

        for session_id in sessions:
            context = await self._get_context(session_id)

            if context.get("state") != WorkflowState.PROPOSED:
                continue

            proposal_time = context.get("timestamp", now)
            if now - proposal_time <= timeout_seconds:
                continue

            plan_data = context["data"]["last_plan"]

            update_done = False
            update_if_state_matches = getattr(
                self.state_store, "update_if_state_matches", None
            )

            if callable(update_if_state_matches):
                update_done = await update_if_state_matches(
                    session_id=session_id,
                    expected_state=WorkflowState.PROPOSED,
                    new_state=WorkflowState.REJECTED,
                    data={"last_plan": plan_data},
                )

            if not update_done:
                # Fallback: non-atomic, but preserves existing interface
                latest_context = await self._get_context(session_id)
                if latest_context.get("state") != WorkflowState.PROPOSED:
                    continue

                await self.state_store.save_context(
                    session_id,
                    {"last_plan": plan_data},
                    state=WorkflowState.REJECTED,
                )

            self.auditor.log(
                session_id,
                "HITL_TIMEOUT_REJECTED",
                {"message": "Proposal auto-rejected due to timeout"},
            )
