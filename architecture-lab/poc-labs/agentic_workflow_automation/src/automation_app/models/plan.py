from pydantic import BaseModel, ConfigDict
from typing import List
from .action import Action

class Plan(BaseModel):
    actions: List[Action] = []
    model_config = ConfigDict(extra="forbid")