"""Content service for managing uploaded content."""
import os
from datetime import datetime
from typing import Optional
from app.models.content import Content, get_file_type, is_allowed_file
from app.services.agent_orchestrator import agent_orchestrator


class ContentService:
    """Service for managing content uploads and processing."""
    
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
        self._contents: dict[str, Content] = {}  # In-memory storage
        self._user_contents: dict[str, list[str]] = {}  # user_id -> content_ids
        
        # Ensure upload directory exists
        os.makedirs(self._upload_dir, exist_ok=True)
    
    def validate_file_type(self, filename: str) -> tuple[bool, Optional[str], Optional[str]]:
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
    
    def upload_content(self, user_id: str, filename: str, 
                       file_data: bytes) -> tuple[Optional[Content], Optional[str]]:
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
        
        # Create content record
        content = Content.create(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_path=""  # Will be set after saving
        )
        
        # Create user-specific upload directory
        user_upload_dir = os.path.join(self._upload_dir, user_id)
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Generate unique filename to avoid collisions
        safe_filename = f"{content.id}_{filename}"
        file_path = os.path.join(user_upload_dir, safe_filename)
        
        try:
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            content.file_path = file_path
            
            # Store content record
            self._contents[content.id] = content
            
            # Track user's content
            if user_id not in self._user_contents:
                self._user_contents[user_id] = []
            self._user_contents[user_id].append(content.id)
            
            return content, None
            
        except IOError as e:
            return None, f"Failed to save file: {str(e)}"
    
    def process_content(self, content_id: str) -> tuple[Optional[Content], Optional[str]]:
        """
        Process uploaded content through ContentAgent.
        
        Args:
            content_id: ID of the content to process.
            
        Returns:
            Tuple of (Content, None) on success, or (None, error_message) on failure.
        """
        content = self._contents.get(content_id)
        if not content:
            return None, "Content not found"
        
        try:
            # Read file content (for text extraction)
            # In a real implementation, this would use proper extractors
            # for video (transcription) and PDF (text extraction)
            content_text = self._extract_text(content)
            
            # Process through ContentAgent
            result = agent_orchestrator.process_content(
                content_text=content_text,
                content_type=content.file_type
            )
            
            if "error" in result:
                return None, result["error"]
            
            # Update content with extracted information
            content.summary = [result.get("summary", "")]
            content.key_points = result.get("key_points", [])
            content.processed_at = datetime.utcnow()
            
            return content, None
            
        except Exception as e:
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
        
        if content.file_type == 'pdf':
            return f"[Extracted text from PDF: {content.filename}]"
        elif content.file_type == 'video':
            return f"[Transcribed text from video: {content.filename}]"
        
        return ""
    
    def get_content(self, content_id: str) -> Optional[Content]:
        """
        Get content by ID.
        
        Args:
            content_id: ID of the content to retrieve.
            
        Returns:
            Content if found, None otherwise.
        """
        return self._contents.get(content_id)
    
    def get_user_contents(self, user_id: str) -> list[Content]:
        """
        Get all content for a user.
        
        Args:
            user_id: ID of the user.
            
        Returns:
            List of Content objects for the user.
        """
        content_ids = self._user_contents.get(user_id, [])
        return [self._contents[cid] for cid in content_ids if cid in self._contents]
    
    def delete_content(self, content_id: str, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Delete content.
        
        Args:
            content_id: ID of the content to delete.
            user_id: ID of the user (for authorization).
            
        Returns:
            Tuple of (success, error_message).
        """
        content = self._contents.get(content_id)
        if not content:
            return False, "Content not found"
        
        if content.user_id != user_id:
            return False, "Not authorized to delete this content"
        
        try:
            # Delete file if it exists
            if content.file_path and os.path.exists(content.file_path):
                os.remove(content.file_path)
            
            # Remove from storage
            del self._contents[content_id]
            
            # Remove from user's content list
            if user_id in self._user_contents:
                self._user_contents[user_id] = [
                    cid for cid in self._user_contents[user_id] 
                    if cid != content_id
                ]
            
            return True, None
            
        except Exception as e:
            return False, f"Failed to delete content: {str(e)}"
    
    def get_content_summary(self, content_id: str) -> Optional[list[str]]:
        """
        Get the summary for processed content.
        
        Args:
            content_id: ID of the content.
            
        Returns:
            List of summary strings, or None if not found/processed.
        """
        content = self._contents.get(content_id)
        if not content or not content.processed_at:
            return None
        return content.summary
    
    def get_content_key_points(self, content_id: str) -> Optional[list[str]]:
        """
        Get the key points for processed content.
        
        Args:
            content_id: ID of the content.
            
        Returns:
            List of key point strings, or None if not found/processed.
        """
        content = self._contents.get(content_id)
        if not content or not content.processed_at:
            return None
        return content.key_points


# Global content service instance
content_service = ContentService()
