from pydantic import BaseModel


class OrchestratorRequest(BaseModel):
    session_id: str
    text: str