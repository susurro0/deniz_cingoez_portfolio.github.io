from pydantic import BaseModel
from typing import Optional, Dict, Any


class ExecutionFailure(BaseModel):
    adapter: str
    method: str
    step_idx: int
    error_type: str          # "TRANSIENT", "PERMISSION", "NOT_SUPPORTED", "UNKNOWN"
    message: str
    raw_error: Optional[str] = None
    context: Dict[str, Any] = {}
