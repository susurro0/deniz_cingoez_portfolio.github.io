from automation_app.models.plan import Plan


class PolicyEngine:
    async def validate_plan(self, plan: Plan) -> bool:
        # Example: PTO must check calendar first
        if not plan.actions:
            return False

        first_action = plan.actions[0]
        if first_action.method != "check_calendar_availability":
            return False

        return True

    async def check_permissions(self, user_id: str, action: str) -> bool:
        # Stub: allow everything
        return True
