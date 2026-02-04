from automation_app.models.action import Action
from automation_app.models.intent import Intent
from automation_app.models.plan import Plan


class TaskPlanner:
    def generate_plan(self, intent: Intent, state: dict) -> Plan:
        if intent.type == "PTO":
            return Plan(actions=[
                Action(
                    adapter="MSGraph",
                    method="check_calendar_availability",
                    params={"date": "Friday"}
                ),
                Action(
                    adapter="Workday",
                    method="book_time_off",
                    params={"dates": ["Friday"]}
                )
            ])

        raise ValueError("Unsupported intent")
