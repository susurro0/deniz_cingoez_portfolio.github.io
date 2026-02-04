from pydantic import BaseModel, ConfigDict


class Action(BaseModel):
    adapter: str        # Name of the adapter to call (e.g., 'Workday', 'MSGraph')
    method: str         # Method name to execute
    params: dict        # Parameters for the action
    model_config = ConfigDict(extra="forbid")