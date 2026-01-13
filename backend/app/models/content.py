"""Content model for uploaded files and processed content."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Content:
    """Model representing uploaded and processed content."""
    
    id: str
    user_id: str
    filename: str
    file_type: str  # 'video' | 'pdf'
    file_path: str
    summary: list[str] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    processed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(cls, user_id: str, filename: str, file_type: str, 
               file_path: str) -> "Content":
        """
        Create a new Content instance.
        
        Args:
            user_id: ID of the user who uploaded the content.
            filename: Original filename.
            file_type: Type of file ('video' or 'pdf').
            file_path: Path where the file is stored.
            
        Returns:
            New Content instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_path=file_path,
            summary=[],
            key_points=[],
            processed_at=None,
            created_at=datetime.utcnow()
        )
    
    def to_dict(self) -> dict:
        """Convert content to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_path": self.file_path,
            "summary": self.summary,
            "key_points": self.key_points,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Content":
        """Create Content instance from dictionary."""
        processed_at = None
        if data.get("processed_at"):
            processed_at = datetime.fromisoformat(data["processed_at"])
        
        created_at = datetime.utcnow()
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            filename=data["filename"],
            file_type=data["file_type"],
            file_path=data["file_path"],
            summary=data.get("summary", []),
            key_points=data.get("key_points", []),
            processed_at=processed_at,
            created_at=created_at
        )


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
