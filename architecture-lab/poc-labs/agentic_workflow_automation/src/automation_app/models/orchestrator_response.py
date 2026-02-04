from typing import Optional, Any
from pydantic import BaseModel
from automation_app.models.workflow_state import WorkflowState

class OrchestratorResponse(BaseModel):
    message: str
    state: Optional[WorkflowState] = None
    plan: Optional[Any] = None
