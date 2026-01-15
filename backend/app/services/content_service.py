"""Content service for managing uploaded content with database persistence."""
import os
from datetime import datetime
from typing import Optional, List, Tuple

from app.database import db
from app.models.content import Content, get_file_type, is_allowed_file
from app.services.agent_orchestrator import agent_orchestrator


class ContentService:
    """Service for managing content uploads and processing with SQLAlchemy persistence."""
    
    def __init__(self, upload_dir: Optional[str] = None):
        """
        Initialize the content service.
        
        Args:
            upload_dir: Directory for storing uploaded files.
                       Defaults to 'uploads' in the backend directory.
        """
        if upload_dir is None:
            # Default to uploads directory in backend
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            upload_dir = os.path.join(backend_dir, 'uploads')
        
        self._upload_dir = upload_dir
        
        # Ensure upload directory exists
        os.makedirs(self._upload_dir, exist_ok=True)
    
    def validate_file_type(self, filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate if a file type is allowed.
        
        Args:
            filename: The filename to validate.
            
        Returns:
            Tuple of (is_valid, file_type, error_message).
        """
        if not filename:
            return False, None, "Filename is required"
        
        file_type = get_file_type(filename)
        
        if file_type is None:
            return False, None, "Only video and PDF files are supported"
        
        return True, file_type, None
    
    def save_content(self, user_id: str, filename: str, content_type: str,
                     file_data: bytes) -> Content:
        """
        Save uploaded content to file system and database.
        
        Args:
            user_id: ID of the user uploading the content.
            filename: Original filename.
            content_type: Type of content ('video' or 'pdf').
            file_data: Raw file bytes.
            
        Returns:
            Content object with saved data.
            
        Raises:
            IOError: If file cannot be saved.
        """
        # Create user-specific upload directory
        user_upload_dir = os.path.join(self._upload_dir, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Create content record first to get ID
        content = Content(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            file_path="",  # Will be set after saving
            file_size=len(file_data),
            processing_status='pending'
        )
        db.session.add(content)
        db.session.flush()  # Get the ID without committing
        
        # Generate unique filename to avoid collisions
        safe_filename = f"{content.id}_{filename}"
        file_path = os.path.join(user_upload_dir, safe_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Update file path
        content.file_path = file_path
        db.session.commit()
        
        return content
    
    def upload_content(self, user_id: str, filename: str, 
                       file_data: bytes) -> Tuple[Optional[Content], Optional[str]]:
        """
        Upload and store content.
        
        Args:
            user_id: ID of the user uploading the content.
            filename: Original filename.
            file_data: Raw file bytes.
            
        Returns:
            Tuple of (Content, None) on success, or (None, error_message) on failure.
        """
        # Validate file type
        is_valid, file_type, error = self.validate_file_type(filename)
        if not is_valid:
            return None, error
        
        try:
            content = self.save_content(
                user_id=user_id,
                filename=filename,
                content_type=file_type,
                file_data=file_data
            )
            return content, None
            
        except IOError as e:
            db.session.rollback()
            return None, f"Failed to save file: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to upload content: {str(e)}"
    
    def update_content_metadata(self, content_id: str, title: Optional[str] = None,
                                summary: Optional[str] = None,
                                key_points: Optional[List[str]] = None,
                                topics: Optional[List[str]] = None) -> Optional[Content]:
        """
        Update content with extracted metadata from AI processing.
        
        Args:
            content_id: ID of the content to update.
            title: Extracted title.
            summary: Extracted summary.
            key_points: List of key points.
            topics: List of topics.
            
        Returns:
            Updated Content object, or None if not found.
        """
        content = Content.query.get(content_id)
        if not content:
            return None
        
        if title is not None:
            content.title = title
        if summary is not None:
            content.summary = summary
        if key_points is not None:
            content.key_points = key_points
        if topics is not None:
            content.topics = topics
        
        content.processing_status = 'complete'
        db.session.commit()
        
        return content
    
    def process_content(self, content_id: str) -> Tuple[Optional[Content], Optional[str]]:
        """
        Process uploaded content through ContentAgent.
        
        Args:
            content_id: ID of the content to process.
            
        Returns:
            Tuple of (Content, None) on success, or (None, error_message) on failure.
        """
        content = Content.query.get(content_id)
        if not content:
            return None, "Content not found"
        
        try:
            # Read file content (for text extraction)
            content_text = self._extract_text(content)
            
            # Process through ContentAgent
            result = agent_orchestrator.process_content(
                content_data=content_text,
                content_type=content.content_type,
                filename=content.filename
            )
            
            # Check for processing failure
            if result.get("processing_status") == "failed":
                content.processing_status = 'failed'
                db.session.commit()
                return None, result.get("error_message", "Processing failed")
            
            # Update content with extracted information
            content.summary = result.get("summary", "")
            content.key_points = result.get("key_points", [])
            content.title = result.get("title", content.filename)
            content.topics = result.get("topics", [])
            content.processing_status = 'complete'
            db.session.commit()
            
            return content, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to process content: {str(e)}"
    
    def _extract_text(self, content: Content) -> str:
        """
        Extract text from content file.
        
        Args:
            content: The content to extract text from.
            
        Returns:
            Extracted text string.
        """
        # Placeholder implementation
        # In a real implementation:
        # - For PDF: Use PyPDF2 or pdfplumber
        # - For video: Use speech-to-text transcription
        
        if content.content_type == 'pdf':
            return f"[Extracted text from PDF: {content.filename}]"
        elif content.content_type == 'video':
            return f"[Transcribed text from video: {content.filename}]"
        
        return ""
    
    def get_user_content(self, user_id: str) -> List[Content]:
        """
        Get all content for a user.
        
        Args:
            user_id: ID of the user.
            
        Returns:
            List of Content objects for the user, ordered by creation date (newest first).
        """
        return Content.query.filter_by(user_id=user_id).order_by(
            Content.created_at.desc()
        ).all()
    
    # Alias for backward compatibility
    def get_user_contents(self, user_id: str) -> List[Content]:
        """Alias for get_user_content for backward compatibility."""
        return self.get_user_content(user_id)
    
    def get_content(self, content_id: str, user_id: Optional[str] = None) -> Optional[Content]:
        """
        Get content by ID, optionally filtered by user.
        
        Args:
            content_id: ID of the content to retrieve.
            user_id: Optional user ID to verify ownership.
            
        Returns:
            Content if found (and owned by user if user_id provided), None otherwise.
        """
        if user_id:
            return Content.query.filter_by(id=content_id, user_id=user_id).first()
        return Content.query.get(content_id)
    
    def delete_content(self, content_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete content and its associated file.
        
        Args:
            content_id: ID of the content to delete.
            user_id: ID of the user (for authorization).
            
        Returns:
            Tuple of (success, error_message).
        """
        content = Content.query.filter_by(id=content_id, user_id=user_id).first()
        
        if not content:
            # Check if content exists but belongs to another user
            exists = Content.query.get(content_id)
            if exists:
                return False, "Not authorized to delete this content"
            return False, "Content not found"
        
        try:
            # Delete file if it exists
            if content.file_path and os.path.exists(content.file_path):
                os.remove(content.file_path)
            
            # Delete database record
            db.session.delete(content)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete content: {str(e)}"
    
    def get_content_summary(self, content_id: str) -> Optional[str]:
        """
        Get the summary for processed content.
        
        Args:
            content_id: ID of the content.
            
        Returns:
            Summary string, or None if not found/processed.
        """
        content = Content.query.get(content_id)
        if not content or content.processing_status != 'complete':
            return None
        return content.summary
    
    def get_content_key_points(self, content_id: str) -> Optional[List[str]]:
        """
        Get the key points for processed content.
        
        Args:
            content_id: ID of the content.
            
        Returns:
            List of key point strings, or None if not found/processed.
        """
        content = Content.query.get(content_id)
        if not content or content.processing_status != 'complete':
            return None
        return content.key_points


# Global content service instance
content_service = ContentService()
