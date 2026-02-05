from automation_app.adapters.base_adapter import EnterpriseAdapter


class MSGraphAdapter(EnterpriseAdapter):

    # -------- EnterpriseAdapter contract --------

    def execute(self, action: str, params: dict) -> dict:
        if action == "send_email":
            return self.send_email(params)

        if action == "create_calendar_event":
            return self.create_calendar_event(params)

        raise ValueError(f"Unsupported MSGraph action: {action}")

    def compensate(self, action: str, params: dict, result: dict) -> None:
        if action == "send_email":
            self.log_email_compensation(result)
            return

        if action == "create_calendar_event":
            self.delete_calendar_event(result["event_id"])
            return

        # Unknown actions are ignored during compensation
        # (never raise in rollback unless you want cascading failures)

    def supported_actions(self) -> set:
        return {
            "send_email",
            "create_calendar_event",
        }

    # -------- Concrete MS Graph operations --------

    def send_email(self, params: dict) -> dict:
        message_id = "MSG-123"
        return {"message_id": message_id}

    def create_calendar_event(self, params: dict) -> dict:
        event_id = "EVT-456"
        return {"event_id": event_id}

    def delete_calendar_event(self, event_id: str) -> None:
        # Idempotent delete
        pass

    def log_email_compensation(self, result: dict) -> None:
        # Semantic compensation (audit / alert / follow-up)
        pass
