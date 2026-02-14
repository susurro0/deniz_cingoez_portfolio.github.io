import uuid
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class FinObsRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    task_type: str = Field(..., description="e.g., 'summarization', 'code', 'general'")
    priority: str = "cost"  # cost, performance, or balanced
    metadata: Dict[str, str] = {}
