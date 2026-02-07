from automation_app.adapters.base_adapter import EnterpriseAdapter


class MSGraphAdapter(EnterpriseAdapter):

    # -------- EnterpriseAdapter contract --------

    async def execute(self, action: str, params: dict) -> dict:
        if action == "send_email":
            return await self.send_email(params)

        if action == "create_calendar_event":
            return await self.create_calendar_event(params)

        raise ValueError(f"Unsupported MSGraph action: {action}")

    async def compensate(self, action: str, params: dict, result: dict) -> None:
        if action == "send_email":
            await self.log_email_compensation(result)
            return

        if action == "create_calendar_event":
            await self.delete_calendar_event(result["event_id"])
            return

        # Unknown actions are ignored during compensation

    def supported_actions(self) -> set:
        return {
            "send_email",
            "create_calendar_event",
        }

    # -------- Concrete MS Graph operations --------

    async def send_email(self, params: dict) -> dict:
        # await ms_graph_client.send_mail(...)
        message_id = "MSG-123"
        return {"message_id": message_id}

    async def create_calendar_event(self, params: dict) -> dict:
        # await ms_graph_client.create_event(...)
        event_id = "EVT-456"
        return {"event_id": event_id}

    async def delete_calendar_event(self, event_id: str) -> None:
        # await ms_graph_client.delete_event(event_id)
        # Idempotent delete
        pass

    async def log_email_compensation(self, result: dict) -> None:
        # async audit / alert / follow-up
        pass
