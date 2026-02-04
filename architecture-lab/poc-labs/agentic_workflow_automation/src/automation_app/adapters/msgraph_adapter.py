class MSGraphAdapter:
    def execute(self, action: str, params: dict) -> dict:
        if action == "check_calendar_availability":
            return {
                "status": "available"
            }

        raise ValueError(f"Unknown MSGraph action: {action}")
