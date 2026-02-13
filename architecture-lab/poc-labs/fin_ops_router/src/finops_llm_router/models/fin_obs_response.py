from typing import Optional, Any, Dict
from pydantic import BaseModel

class FinObsResponse(BaseModel):
    id: str
    content: str
    model_used: str
    provider: str
    usage: Dict[str, int]  # input_tokens, output_tokens
    cost_estimated: float
    latency_ms: float

