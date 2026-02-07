from typing import List
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
