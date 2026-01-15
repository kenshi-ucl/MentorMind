"""
Call and CallParticipant models for voice/video calls.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.database import db


class Call(db.Model):
    """Model representing a voice or video call."""
    __tablename__ = 'calls'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    initiator_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    call_type = Column(String(20), nullable=False)  # 'voice', 'video'
    context_type = Column(String(20), nullable=False)  # 'direct', 'group'
    context_id = Column(String(36), nullable=False)  # direct_chat_id or group_id
    status = Column(String(20), default='ringing')  # 'ringing', 'active', 'ended', 'missed', 'declined'
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    initiator = db.relationship('User', foreign_keys=[initiator_id])
    participants = db.relationship('CallParticipant', backref='call', lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    def to_dict(self, include_participants=False):
        """Convert call to dictionary."""
        result = {
            'id': self.id,
            'initiatorId': self.initiator_id,
            'initiatorName': self.initiator.name if self.initiator else None,
            'callType': self.call_type,
            'contextType': self.context_type,
            'contextId': self.context_id,
            'status': self.status,
            'startedAt': self.started_at.isoformat() if self.started_at else None,
            'endedAt': self.ended_at.isoformat() if self.ended_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'duration': self._calculate_duration()
        }
        if include_participants:
            result['participants'] = [p.to_dict() for p in self.participants.all()]
        return result
    
    def _calculate_duration(self):
        """Calculate call duration in seconds."""
        if self.started_at and self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds())
        elif self.started_at:
            return int((datetime.utcnow() - self.started_at).total_seconds())
        return 0


class CallParticipant(db.Model):
    """Model representing a participant in a call."""
    __tablename__ = 'call_participants'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_id = Column(String(36), ForeignKey('calls.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='invited')  # 'invited', 'ringing', 'joined', 'left', 'declined'
    is_muted = Column(Boolean, default=False)
    is_video_off = Column(Boolean, default=False)
    is_screen_sharing = Column(Boolean, default=False)
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    
    def to_dict(self):
        """Convert call participant to dictionary."""
        return {
            'id': self.id,
            'callId': self.call_id,
            'userId': self.user_id,
            'userName': self.user.name if self.user else None,
            'status': self.status,
            'isMuted': self.is_muted,
            'isVideoOff': self.is_video_off,
            'isScreenSharing': self.is_screen_sharing,
            'joinedAt': self.joined_at.isoformat() if self.joined_at else None,
            'leftAt': self.left_at.isoformat() if self.left_at else None
        }
