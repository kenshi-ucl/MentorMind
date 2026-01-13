"""User model for authentication."""
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    """User model representing authenticated and anonymous users."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: Optional[str] = None
    name: str = ""
    password_hash: Optional[str] = None
    is_anonymous: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary for API responses."""
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_anonymous': self.is_anonymous,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat()
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create a User instance from a dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            email=data.get('email'),
            name=data.get('name', ''),
            password_hash=data.get('password_hash'),
            is_anonymous=data.get('is_anonymous', False),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.utcnow(),
            last_login=datetime.fromisoformat(data['last_login']) if 'last_login' in data else datetime.utcnow()
        )
