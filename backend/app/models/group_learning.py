"""
GroupLearning model for collaborative learning sessions.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.database import db


class GroupLearning(db.Model):
    """Model representing a group learning session."""
    __tablename__ = 'group_learning'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id])
    members = db.relationship('GroupMember', backref='group', lazy='dynamic',
                             cascade='all, delete-orphan')
    messages = db.relationship('GroupMessage', backref='group', lazy='dynamic',
                              order_by='GroupMessage.created_at', cascade='all, delete-orphan')
    
    def to_dict(self, include_members=False):
        """Convert group to dictionary."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'creatorId': self.creator_id,
            'creatorName': self.creator.name if self.creator else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastActivityAt': self.last_activity_at.isoformat() if self.last_activity_at else None,
            'memberCount': self.members.filter_by(status='active').count()
        }
        if include_members:
            result['members'] = [m.to_dict() for m in self.members.filter_by(status='active').all()]
        return result
