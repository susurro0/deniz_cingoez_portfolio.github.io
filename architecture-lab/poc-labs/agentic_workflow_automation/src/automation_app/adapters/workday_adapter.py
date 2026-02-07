from typing import Any, Coroutine

from automation_app.adapters.base_adapter import EnterpriseAdapter


class WorkdayAdapter(EnterpriseAdapter):

    async def execute(self, action: str, params: dict) -> dict:
        if action == "create_time_off":
            return await self.create_time_off(params)
        raise ValueError(f"Unsupported action: {action}")

    async def compensate(self, action: str, params: dict, result: dict) -> None:
        if action == "create_time_off":
            request_id = result.get("request_id")
            if request_id:
                await self.cancel_time_off(request_id)

    # ---- Explicit API calls ----
    def supported_actions(self) -> set[str]:
        return {"create_time_off"}

    async def create_time_off(self, params: dict) -> dict:
        # Call Workday API
        return {"request_id": "WD123"}

    async def cancel_time_off(self, request_id: str) -> None:
        # Idempotent cancel
        pass