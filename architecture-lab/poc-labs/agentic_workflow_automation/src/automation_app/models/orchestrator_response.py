from pydantic import BaseModel


class OrchestratorResponse(BaseModel):
    message: str