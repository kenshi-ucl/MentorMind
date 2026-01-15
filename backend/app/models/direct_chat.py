"""
DirectChat model for one-on-one messaging between friends.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database import db


class DirectChat(db.Model):
    """Model representing a direct chat between two users."""
    __tablename__ = 'direct_chats'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user1_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    user2_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    messages = db.relationship('DirectMessage', backref='chat', lazy='dynamic',
                              order_by='DirectMessage.created_at', cascade='all, delete-orphan')
    
    def to_dict(self, current_user_id=None):
        """Convert direct chat to dictionary."""
        # Determine the other user in the chat
        other_user = self.user2 if self.user1_id == current_user_id else self.user1
        
        return {
            'id': self.id,
            'user1Id': self.user1_id,
            'user2Id': self.user2_id,
            'otherUser': other_user.to_dict() if other_user else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastMessageAt': self.last_message_at.isoformat() if self.last_message_at else None
        }
    
    def get_other_user_id(self, current_user_id):
        """Get the ID of the other user in the chat."""
        return self.user2_id if self.user1_id == current_user_id else self.user1_id
