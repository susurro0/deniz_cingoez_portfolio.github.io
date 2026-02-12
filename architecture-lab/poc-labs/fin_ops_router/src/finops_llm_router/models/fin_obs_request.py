from pydantic import BaseModel, ConfigDict


class FinObsRequest(BaseModel):
    prompt: str
    model_type: str
