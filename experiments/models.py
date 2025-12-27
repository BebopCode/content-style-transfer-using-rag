# models.py
from sqlalchemy import Column, Integer, String, DateTime, LargeBinary, JSON, ForeignKey
from .database import Base

class EmailDB(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, nullable=True)
    parent_message_id = Column(String, nullable=True)
    references = Column(JSON, nullable=True)
    sender = Column(String, index=True)
    receiver = Column(String)
    content = Column(String)
    subject = Column(String)
    sent_at = Column(DateTime)

    def __repr__(self):
        return f"EmailDB(id={self.id}, Message ID={self.message_id}, Parent Message={self.parent_message_id}, references={self.references} sender='{self.sender}', receiver='{self.receiver}' subject='{self.subject} date={self.sent_at})"