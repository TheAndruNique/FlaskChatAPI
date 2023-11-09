from typing import Optional
import uuid
from pydantic import BaseModel, Field


class CreateGroupChatModel(BaseModel):
    users_id: Optional[list[int]] = Field(default=None)
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))