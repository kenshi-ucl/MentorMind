"""
UserPresence model for tracking online status.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.database import db


class UserPresence(db.Model):
    """Model representing a user's online presence status."""
    __tablename__ = 'user_presence'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    socket_id = Column(String(255), nullable=True)
    current_status = Column(String(50), default='available')  # 'available', 'busy', 'away', 'in_call'
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='presence')
    
    def to_dict(self):
        """Convert presence to dictionary."""
        return {
            'userId': self.user_id,
            'isOnline': self.is_online,
            'lastSeen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.current_status
        }
