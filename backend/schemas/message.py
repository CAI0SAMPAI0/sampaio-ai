from pydantic import BaseModel


class MessageIn(BaseModel):
    message: str


class MessageOut(BaseModel):
    message: str
    response: str
    conversation_title: str | None = None