"""
Message models for direct and group messaging.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from app.database import db


class DirectMessage(db.Model):
    """Model for messages in direct chats."""
    __tablename__ = 'direct_messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String(36), ForeignKey('direct_chats.id'), nullable=False)
    sender_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    read_by = Column(JSON, default=list)  # List of user IDs who have read the message
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'chatId': self.chat_id,
            'senderId': self.sender_id,
            'senderName': self.sender.name if self.sender else None,
            'content': self.content,
            'readBy': self.read_by or [],
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


class GroupMessage(db.Model):
    """Model for messages in group learning sessions."""
    __tablename__ = 'group_messages'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey('group_learning.id'), nullable=False)
    sender_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    read_by = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'groupId': self.group_id,
            'senderId': self.sender_id,
            'senderName': self.sender.name if self.sender else None,
            'content': self.content,
            'readBy': self.read_by or [],
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
