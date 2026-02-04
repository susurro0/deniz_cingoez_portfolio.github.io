from pydantic import BaseModel


class UserRequest(BaseModel):
    session_id: str
    text: str