"""
GroupMember model for tracking group membership.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database import db


class GroupMember(db.Model):
    """Model representing membership in a group learning session."""
    __tablename__ = 'group_members'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey('group_learning.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    role = Column(String(20), default='member')  # 'creator', 'admin', 'member'
    status = Column(String(20), default='pending')  # 'pending', 'active', 'left', 'removed'
    joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    
    def to_dict(self):
        """Convert group member to dictionary."""
        return {
            'id': self.user_id,  # Use user_id as the member id for frontend
            'memberId': self.id,
            'groupId': self.group_id,
            'userId': self.user_id,
            'name': self.user.name if self.user else None,
            'userName': self.user.name if self.user else None,
            'userEmail': self.user.email if self.user else None,
            'role': self.role,
            'status': self.status,
            'joinedAt': self.joined_at.isoformat() if self.joined_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
