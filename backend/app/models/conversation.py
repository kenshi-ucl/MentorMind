"""
Conversation and Message models for chat history persistence.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import db


class Conversation(db.Model):
    """Model for storing chat conversations."""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', backref='conversations')
    messages = relationship('Message', backref='conversation', lazy='dynamic', 
                          order_by='Message.created_at', cascade='all, delete-orphan')
    
    def to_dict(self, include_messages=False):
        """Convert conversation to dictionary."""
        result = {
            'id': self.id,
            'userId': self.user_id,
            'title': self.title or 'New Conversation',
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'isActive': self.is_active,
            'messageCount': self.messages.count()
        }
        
        if include_messages:
            result['messages'] = [msg.to_dict() for msg in self.messages.all()]
        
        return result
    
    def get_context_messages(self, limit=20):
        """
        Get recent messages for AI context.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with role and content
        """
        recent_messages = self.messages.order_by(Message.created_at.desc()).limit(limit).all()
        # Reverse to get chronological order
        recent_messages = list(reversed(recent_messages))
        
        return [
            {'role': msg.role, 'content': msg.content}
            for msg in recent_messages
        ]


class Message(db.Model):
    """Model for storing individual chat messages."""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_id = Column(String(36), nullable=True)  # UUID for frontend reference
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'conversationId': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'messageId': self.message_id,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'timestamp': self.created_at.isoformat() if self.created_at else None
        }
