from pydantic import BaseModel, ConfigDict


class Intent(BaseModel):
    type: str       # e.g., 'PTO', 'Meeting'
    entity: str     # e.g., 'Friday', 'Team Meeting'
    model_config = ConfigDict(extra="forbid")