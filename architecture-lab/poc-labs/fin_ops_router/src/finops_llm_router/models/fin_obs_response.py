from typing import Optional, Any
from pydantic import BaseModel

class FinObsResponse(BaseModel):
    prompt: str
    response: str
    model_type: str

