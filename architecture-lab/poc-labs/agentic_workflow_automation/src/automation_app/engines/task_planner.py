from __future__ import annotations

from typing import List

from automation_app.config.constants import RecoveryDecision
from automation_app.models.action import Action
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan


class TaskPlanner:
    """
    Async TaskPlanner: generates executable Plans from Intents.
    Actions are aligned with the implemented adapters.
    """

    async def generate_plan(self, intent: Intent, state: dict) -> Plan:
        """
        Generates a Plan for the given Intent and user state.
        """
        actions: List[Action] = []

        # Example: PTO / Time Off request
        if intent.name == "REQUEST_TIME_OFF":
            user_id = state.get("user_id")

            # 1. Check calendar availability (MSGraph)
            actions.append(
                Action(
                    adapter="MSGraph",
                    method="create_calendar_event",  # Matches MSGraphAdapter
                    params={
                        "date": intent.entities.get("date"),
                        "title": "Time off check",
                        "user_id": user_id
                    }
                )
            )

            # 2. Book time off (Workday)
            actions.append(
                Action(
                    adapter="Workday",
                    method="create_time_off",  # Matches WorkdayAdapter
                    params={
                        "dates": [intent.entities.get("date")],
                        "user_id": user_id
                    }
                )
            )

            return Plan(actions=actions)

        # Default: unsupported intent
        raise ValueError(f"Unsupported intent: {intent.name}")

    async def repair_plan(
            self,
            *,
            failed_plan: Plan,
            failed_action: Action,
            decision: RecoveryDecision,
    ) -> Plan | None:

        if decision == RecoveryDecision.NOT_SUPPORTED:
            return self._replace_unsupported_action(failed_plan, failed_action)

        if decision == RecoveryDecision.PERMISSION:
            step_idx = failed_plan.actions.index(failed_action)
            return self._insert_approval_step(
                failed_plan,
                step_idx=step_idx,
                reason="User approval required for this action",
            )

        # unrecoverable
        return None

    def _replace_unsupported_action(self, plan, failed_action):
        new_actions = []

        for action in plan.actions:
            if action == failed_action:
                new_actions.append(
                    Action(
                        adapter="notification",
                        method="send",
                        params={**action.params, "reason": "Unsupported action replaced with notification"}
                    )
                )
            else:
                new_actions.append(action)

        return Plan(actions=new_actions)

    def _insert_approval_step(self, plan: Plan, step_idx: int, reason: str = None) -> Plan:
        """
        Inserts an approval step *before* the action at step_idx.
        Used for self-correction / failed actions.
        """
        approval_action = Action(
            adapter="HITL",  # or your human review adapter
            method="request_approval",
            params={
                "reason": reason or "Action requires review",
                "original_step": step_idx,
            }
        )

        # Insert before the failing step
        new_actions = plan.actions[:step_idx] + [approval_action] + plan.actions[step_idx:]
        return Plan(actions=new_actions)