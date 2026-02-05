from automation_app.adapters.base_adapter import EnterpriseAdapter


class WorkdayAdapter(EnterpriseAdapter):

    def execute(self, action: str, params: dict) -> dict:
        if action == "create_time_off":
            return self.create_time_off(params)
        raise ValueError(f"Unsupported action: {action}")

    def compensate(self, action: str, params: dict, result: dict) -> None:
        if action == "create_time_off":
            request_id = result.get("request_id")
            if request_id:
                self.cancel_time_off(request_id)

    # ---- Explicit API calls ----
    def supported_actions(self) -> set[str]:
        return {"create_time_off"}

    def create_time_off(self, params: dict) -> dict:
        # Call Workday API
        return {"request_id": "WD123"}

    def cancel_time_off(self, request_id: str) -> None:
        # Idempotent cancel
        pass