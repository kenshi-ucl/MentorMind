"""
Content model for database persistence.

Defines the Content table with SQLAlchemy ORM for storing uploaded file metadata.
"""
import uuid
import json
from datetime import datetime
from typing import Optional, List

from app.database import db


class Content(db.Model):
    """Content model representing uploaded files and their metadata."""
    
    __tablename__ = 'contents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    title = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    key_points_json = db.Column(db.Text, nullable=True)  # JSON array
    topics_json = db.Column(db.Text, nullable=True)  # JSON array
    processing_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Content {self.id}: {self.filename}>'
    
    @property
    def key_points(self) -> List[str]:
        """Get key points as a list."""
        return json.loads(self.key_points_json) if self.key_points_json else []
    
    @key_points.setter
    def key_points(self, value: Optional[List[str]]) -> None:
        """Set key points from a list."""
        self.key_points_json = json.dumps(value) if value else None
    
    @property
    def topics(self) -> List[str]:
        """Get topics as a list."""
        return json.loads(self.topics_json) if self.topics_json else []
    
    @topics.setter
    def topics(self, value: Optional[List[str]]) -> None:
        """Set topics from a list."""
        self.topics_json = json.dumps(value) if value else None
    
    def to_dict(self) -> dict:
        """Convert content to dictionary for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'content_type': self.content_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'title': self.title,
            'summary': self.summary,
            'key_points': self.key_points,
            'topics': self.topics,
            'processing_status': self.processing_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Content':
        """Create a Content instance from a dictionary."""
        content = cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data['user_id'],
            filename=data['filename'],
            content_type=data['content_type'],
            file_path=data['file_path'],
            file_size=data.get('file_size', 0),
            title=data.get('title'),
            summary=data.get('summary'),
            processing_status=data.get('processing_status', 'pending'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.utcnow()
        )
        # Set JSON properties through setters
        content.key_points = data.get('key_points', [])
        content.topics = data.get('topics', [])
        return content


# Allowed file types for upload
ALLOWED_FILE_TYPES = {'video', 'pdf'}

# Allowed file extensions mapped to file types
ALLOWED_EXTENSIONS = {
    # Video extensions
    '.mp4': 'video',
    '.avi': 'video',
    '.mov': 'video',
    '.mkv': 'video',
    '.webm': 'video',
    # PDF extension
    '.pdf': 'pdf'
}


def get_file_type(filename: str) -> Optional[str]:
    """
    Get the file type based on filename extension.
    
    Args:
        filename: The filename to check.
        
    Returns:
        'video', 'pdf', or None if not allowed.
    """
    if not filename:
        return None
    
    # Get the extension (lowercase)
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    return ALLOWED_EXTENSIONS.get(ext)


def is_allowed_file(filename: str) -> bool:
    """
    Check if a file is allowed based on its extension.
    
    Args:
        filename: The filename to check.
        
    Returns:
        True if the file type is allowed, False otherwise.
    """
    return get_file_type(filename) is not None
