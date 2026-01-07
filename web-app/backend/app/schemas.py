from pydantic import BaseModel
from typing import List, Optional

from datetime import datetime
class EmailCreate(BaseModel):
    sender: str
    receiver: str
    content: str
    subject: str
    sent_at: datetime

class ThreadMessageSchema(BaseModel):
    message_id: str
    sender: str
    receiver: str
    subject: str
    content: str
    sent_at: Optional[str] = None

class Generate(BaseModel):
    sender: str
    receiver: str
    content: str
    custom_prompt: str
    thread_messages: List[ThreadMessageSchema] = []
