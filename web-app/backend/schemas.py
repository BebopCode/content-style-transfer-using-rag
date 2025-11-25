from pydantic import BaseModel
from datetime import datetime
class EmailCreate(BaseModel):
    sender: str
    receiver: str
    content: str
    subject: str
    sent_at: datetime

class Generate(BaseModel):
    sender: str
    receiver: str
    content: str
    custom_prompt: str


