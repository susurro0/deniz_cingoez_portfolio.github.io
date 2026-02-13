from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class FinObsRequest(BaseModel):
    prompt: str
    task_type: str = Field(..., description="e.g., 'summarization', 'code', 'general'")
    priority: str = "cost"  # cost, performance, or balanced
    metadata: Dict[str, str] = {}
