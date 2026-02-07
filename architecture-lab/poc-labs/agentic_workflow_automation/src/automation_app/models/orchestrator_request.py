from pydantic import BaseModel


from pydantic import BaseModel
from typing import Optional

class OrchestratorRequest(BaseModel):
    session_id: str
    text: str
    user_id: Optional[str] = "anonymous"
    role: Optional[str] = None
    department: Optional[str] = None
