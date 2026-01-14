"""
User model for database persistence.

Defines the User table with SQLAlchemy ORM for storing registered and anonymous users.
"""
import uuid
from datetime import datetime
from typing import Optional

from app.database import db


class User(db.Model):
    """User model representing authenticated and anonymous users."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    contents = db.relationship('Content', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    quiz_results = db.relationship('QuizResult', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.id}: {self.email or "anonymous"}>'
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary for API responses."""
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_anonymous': self.is_anonymous,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
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
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow(),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else datetime.utcnow()
        )
