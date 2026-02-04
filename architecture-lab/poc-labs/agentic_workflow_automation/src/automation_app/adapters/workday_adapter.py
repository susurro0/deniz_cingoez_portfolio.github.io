class WorkdayAdapter:
    def execute(self, action: str, params: dict) -> dict:
        if action == "book_time_off":
            return {
                "status": "success",
                "reference": "WD-123"
            }

        raise ValueError(f"Unknown Workday action: {action}")
