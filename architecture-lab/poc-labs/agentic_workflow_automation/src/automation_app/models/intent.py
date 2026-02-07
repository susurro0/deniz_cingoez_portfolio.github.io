from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class Intent(BaseModel):
    name: str                     # e.g. "REQUEST_TIME_OFF"
    adapter: str                  # e.g. "Workday"
    method: str                   # e.g. "create_time_off"
    entities: Dict[str, Any] = {} # extracted fields (dates, recipients, etc.)

    model_config = ConfigDict(extra="forbid")
