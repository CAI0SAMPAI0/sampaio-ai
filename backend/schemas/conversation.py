from datetime import datetime
from pydantic import BaseModel


class ConversationOut(BaseModel):
    id:         int
    title:      str | None
    created_at: datetime

    model_config = {"from_attributes": True}