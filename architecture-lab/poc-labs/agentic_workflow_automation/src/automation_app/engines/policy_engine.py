from types import SimpleNamespace
from typing import List, Dict, Any

from automation_app.audit.audit_logger import AuditLogger
from automation_app.models.plan import Plan


class PolicyEngine:
    """
    Enterprise Policy-as-Code engine.

    Characteristics:
    - Deny by default
    - Explicit allow / deny rules
    - Auditable (rule IDs logged)
    - Context-aware (role, department, etc.)
    """

    def __init__(self, rules: List[Dict[str, Any]] = None, auditor=AuditLogger):
        self.rules = rules or []
        self.auditor = auditor

    async def validate_plan(self, plan: Plan, user_context: dict = None) -> bool:
        """
        Validate every action in a Plan.
        All actions must be allowed for the plan to pass.
        """
        user_context = user_context or {}

        # Empty plan is allowed (planner bug should be handled elsewhere)
        if not plan.actions:
            return True

        for action in plan.actions:
            allowed, matched_rules = await self._is_action_allowed(action, user_context)

            if not allowed:
                self.auditor.log(
                    user_context.get("user_id", "anonymous"),
                    "POLICY_VIOLATION",
                    {
                        "adapter": action.adapter,
                        "method": action.method,
                        "matched_rules": matched_rules,
                        "user_context": user_context,
                    },
                )
                return False

        return True

    async def check_permissions(
        self,
        user_id: str,
        action_string: str,
        user_context: dict = None
    ) -> bool:
        """
        Check permissions for UI / frontend use.
        action_string format: "AdapterName.method"
        """
        user_context = user_context or {}
        user_context["user_id"] = user_id

        try:
            adapter, method = action_string.split(".", 1)
        except ValueError:
            return False

        mock_action = SimpleNamespace(adapter=adapter, method=method)
        allowed, _ = await self._is_action_allowed(mock_action, user_context)
        return allowed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _is_action_allowed(self, action: Any, user_context: dict) -> tuple[bool, list]:
        """
        Core rule evaluation.
        Returns (allowed: bool, matched_rule_ids: list[str])
        """
        if user_context.get("role") == "SuperUser":
            return True, ["SUPERUSER_BYPASS"]

        if not self.rules:
            return False, []

        applicable_rules = [
            rule for rule in self.rules
            if rule["target"]["adapter"] == action.adapter
            and rule["target"]["method"] == action.method
        ]

        matched_rule_ids = []

        for rule in applicable_rules:
            conditions = rule.get("conditions", {})

            role_ok = (
                "roles" not in conditions
                or user_context.get("role") in conditions["roles"]
            )

            dept_ok = (
                "departments" not in conditions
                or user_context.get("department") in conditions["departments"]
            )

            if role_ok and dept_ok:
                matched_rule_ids.append(rule["id"])

                if rule["effect"] == "deny":
                    return False, matched_rule_ids

                if rule["effect"] == "allow":
                    return True, matched_rule_ids

        # No rule allowed the action
        return False, matched_rule_ids
