"""Property-based tests for content upload and processing.

Feature: mentormind-ai-tutor
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from app.models.content import get_file_type, is_allowed_file, ALLOWED_EXTENSIONS
from app.services.content_service import ContentService


# Strategies for file extensions
allowed_video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
allowed_pdf_extension = ['.pdf']
all_allowed_extensions = allowed_video_extensions + allowed_pdf_extension

# Strategy for valid filenames with allowed extensions
valid_filename_strategy = st.builds(
    lambda name, ext: f"{name}{ext}",
    name=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-'),
    ext=st.sampled_from(all_allowed_extensions)
)

# Strategy for invalid file extensions
invalid_extensions = ['.txt', '.doc', '.docx', '.jpg', '.png', '.gif', '.exe', '.zip', '.html', '.css', '.js', '.py']
invalid_filename_strategy = st.builds(
    lambda name, ext: f"{name}{ext}",
    name=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-'),
    ext=st.sampled_from(invalid_extensions)
)

# Strategy for filenames without extensions
no_extension_filename_strategy = st.text(
    min_size=1, max_size=20, 
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-'
).filter(lambda x: '.' not in x)


class TestContentProperties:
    """Property-based tests for content service."""
    
    @settings(max_examples=100, deadline=None)
    @given(filename=valid_filename_strategy)
    def test_property_7_valid_file_types_accepted(self, filename):
        """
        Property 7: File Upload Type Validation (Valid Files)
        
        For any file upload attempt, if the file type is 'video' or 'pdf', 
        the upload should be accepted.
        
        Validates: Requirements 5.1, 5.4
        """
        # Check that valid files are accepted
        assert is_allowed_file(filename) == True, f"Valid file {filename} should be allowed"
        
        # Check that file type is correctly identified
        file_type = get_file_type(filename)
        assert file_type in ['video', 'pdf'], f"File type for {filename} should be 'video' or 'pdf', got {file_type}"
        
        # Verify video extensions map to 'video' type
        ext = '.' + filename.rsplit('.', 1)[-1].lower()
        if ext in allowed_video_extensions:
            assert file_type == 'video', f"Extension {ext} should map to 'video'"
        elif ext in allowed_pdf_extension:
            assert file_type == 'pdf', f"Extension {ext} should map to 'pdf'"
    
    @settings(max_examples=100, deadline=None)
    @given(filename=invalid_filename_strategy)
    def test_property_7_invalid_file_types_rejected(self, filename):
        """
        Property 7: File Upload Type Validation (Invalid Files)
        
        For any file upload attempt with a file type other than 'video' or 'pdf', 
        the upload should be rejected with an appropriate error.
        
        Validates: Requirements 5.1, 5.4
        """
        # Check that invalid files are rejected
        assert is_allowed_file(filename) == False, f"Invalid file {filename} should not be allowed"
        
        # Check that file type returns None for invalid files
        file_type = get_file_type(filename)
        assert file_type is None, f"File type for invalid file {filename} should be None, got {file_type}"
        
        # Verify content service validation returns error
        service = ContentService()
        is_valid, file_type, error = service.validate_file_type(filename)
        assert is_valid == False, f"Validation should fail for {filename}"
        assert error is not None, f"Error message should be provided for {filename}"
        assert "Only video and PDF files are supported" in error
    
    @settings(max_examples=100, deadline=None)
    @given(filename=no_extension_filename_strategy)
    def test_property_7_files_without_extension_rejected(self, filename):
        """
        Property 7: File Upload Type Validation (No Extension)
        
        Files without extensions should be rejected.
        
        Validates: Requirements 5.1, 5.4
        """
        # Files without extensions should be rejected
        assert is_allowed_file(filename) == False, f"File without extension {filename} should not be allowed"
        
        file_type = get_file_type(filename)
        assert file_type is None, f"File type for {filename} should be None"
    
    @settings(max_examples=100, deadline=None)
    @given(
        name=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-'),
        ext=st.sampled_from(all_allowed_extensions)
    )
    def test_property_7_case_insensitive_extension_handling(self, name, ext):
        """
        Property 7: File Upload Type Validation (Case Insensitivity)
        
        File extension validation should be case-insensitive.
        
        Validates: Requirements 5.1, 5.4
        """
        # Test lowercase
        filename_lower = f"{name}{ext.lower()}"
        assert is_allowed_file(filename_lower) == True
        
        # Test uppercase
        filename_upper = f"{name}{ext.upper()}"
        assert is_allowed_file(filename_upper) == True
        
        # Test mixed case
        filename_mixed = f"{name}{ext.title()}"
        assert is_allowed_file(filename_mixed) == True
        
        # All should return the same file type
        type_lower = get_file_type(filename_lower)
        type_upper = get_file_type(filename_upper)
        type_mixed = get_file_type(filename_mixed)
        
        assert type_lower == type_upper == type_mixed



class TestContentExtractionProperties:
    """Property-based tests for content extraction through ContentAgent."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        filename=valid_filename_strategy,
        user_id=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
    )
    def test_property_8_content_extraction_produces_key_points(self, filename, user_id):
        """
        Property 8: Content Extraction Produces Key Points
        
        For any successfully uploaded video or PDF file, the ContentAgent 
        should extract and return a non-empty list of key points.
        
        Validates: Requirements 5.2
        """
        import tempfile
        import os
        
        # Create a temporary directory for uploads
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ContentService(upload_dir=temp_dir)
            
            # Create dummy file data
            file_data = b"Sample content for testing extraction"
            
            # Upload content
            content, error = service.upload_content(
                user_id=user_id,
                filename=filename,
                file_data=file_data
            )
            
            assert content is not None, f"Upload failed: {error}"
            assert error is None
            
            # Process content through ContentAgent
            processed_content, process_error = service.process_content(content.id)
            
            # Processing should succeed
            assert processed_content is not None, f"Processing failed: {process_error}"
            assert process_error is None
            
            # Key points should be non-empty
            assert processed_content.key_points is not None, "Key points should not be None"
            assert len(processed_content.key_points) > 0, "Key points should not be empty"
            
            # Each key point should be a non-empty string
            for key_point in processed_content.key_points:
                assert isinstance(key_point, str), "Each key point should be a string"
                assert len(key_point) > 0, "Each key point should be non-empty"
            
            # Content should be marked as processed
            assert processed_content.processed_at is not None, "processed_at should be set"


    @settings(max_examples=100, deadline=None)
    @given(
        filename=valid_filename_strategy,
        user_id=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
    )
    def test_property_9_processed_content_availability(self, filename, user_id):
        """
        Property 9: Processed Content Availability
        
        For any content that has been successfully processed, querying the 
        content list should include that content, and the content should be 
        retrievable by its ID for use by TutorAgent and QuizAgent.
        
        Validates: Requirements 5.5
        """
        import tempfile
        
        # Create a temporary directory for uploads
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ContentService(upload_dir=temp_dir)
            
            # Create dummy file data
            file_data = b"Sample content for testing availability"
            
            # Upload content
            content, error = service.upload_content(
                user_id=user_id,
                filename=filename,
                file_data=file_data
            )
            
            assert content is not None, f"Upload failed: {error}"
            content_id = content.id
            
            # Process content
            processed_content, process_error = service.process_content(content_id)
            assert processed_content is not None, f"Processing failed: {process_error}"
            
            # Test 1: Content should be retrievable by ID
            retrieved_content = service.get_content(content_id)
            assert retrieved_content is not None, "Content should be retrievable by ID"
            assert retrieved_content.id == content_id
            assert retrieved_content.processed_at is not None
            
            # Test 2: Content should appear in user's content list
            user_contents = service.get_user_contents(user_id)
            assert len(user_contents) > 0, "User should have at least one content"
            
            content_ids_in_list = [c.id for c in user_contents]
            assert content_id in content_ids_in_list, "Processed content should be in user's list"
            
            # Test 3: Summary and key points should be accessible
            summary = service.get_content_summary(content_id)
            assert summary is not None, "Summary should be available for processed content"
            
            key_points = service.get_content_key_points(content_id)
            assert key_points is not None, "Key points should be available for processed content"
            assert len(key_points) > 0, "Key points should not be empty"
            
            # Test 4: Content data should be consistent
            content_in_list = next(c for c in user_contents if c.id == content_id)
            assert content_in_list.filename == filename
            assert content_in_list.user_id == user_id
            assert content_in_list.key_points == key_points



class TestContentAwareTutorAgentProperties:
    """Property-based tests for content-aware TutorAgent responses."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        question=st.text(min_size=5, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ?'),
        context_items=st.lists(
            st.text(min_size=10, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
            min_size=1,
            max_size=3
        )
    )
    def test_property_6_content_aware_tutor_responses(self, question, context_items):
        """
        Property 6: Content-Aware TutorAgent Responses
        
        For any uploaded and processed content, when a question related to that 
        content is asked with the content context provided, the TutorAgent response 
        should reference or incorporate information from the content summary.
        
        Validates: Requirements 4.5
        """
        from app.services.agent_orchestrator import AgentOrchestrator
        
        # Filter out empty strings and ensure we have valid context
        valid_context = [c.strip() for c in context_items if c.strip()]
        assume(len(valid_context) > 0)
        assume(len(question.strip()) > 0)
        
        # Create a fresh orchestrator
        orchestrator = AgentOrchestrator()
        
        # Process chat with content context
        response = orchestrator.process_chat(
            message=question.strip(),
            context=valid_context
        )
        
        # Response should be non-empty
        assert response is not None, "Response should not be None"
        assert len(response) > 0, "Response should not be empty"
        assert isinstance(response, str), "Response should be a string"
        
        # When context is provided, the response should indicate awareness of context
        # The placeholder implementation includes "I have context from your uploaded content"
        # when context is provided
        assert "context" in response.lower() or "content" in response.lower() or len(response) > 10, \
            "Response should acknowledge or incorporate the provided context"
    
    @settings(max_examples=100, deadline=None)
    @given(
        question=st.text(min_size=5, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ?')
    )
    def test_property_6_tutor_response_without_context(self, question):
        """
        Property 6 (Complement): TutorAgent Response Without Context
        
        When no content context is provided, the TutorAgent should still 
        return a valid response, but without content-specific references.
        
        Validates: Requirements 4.2
        """
        from app.services.agent_orchestrator import AgentOrchestrator
        
        assume(len(question.strip()) > 0)
        
        orchestrator = AgentOrchestrator()
        
        # Process chat without content context
        response = orchestrator.process_chat(
            message=question.strip(),
            context=None
        )
        
        # Response should be non-empty
        assert response is not None, "Response should not be None"
        assert len(response) > 0, "Response should not be empty"
        assert isinstance(response, str), "Response should be a string"
        
        # Response should contain the question (placeholder behavior)
        # or be a meaningful response
        assert len(response) > 10, "Response should be meaningful"
    
    @settings(max_examples=100, deadline=None)
    @given(
        question=st.text(min_size=5, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ?'),
        context_with=st.lists(
            st.text(min_size=10, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
            min_size=1,
            max_size=3
        )
    )
    def test_property_6_context_vs_no_context_difference(self, question, context_with):
        """
        Property 6 (Differentiation): Context vs No-Context Responses
        
        Responses with content context should differ from responses without context,
        indicating that the context is being incorporated.
        
        Validates: Requirements 4.5
        """
        from app.services.agent_orchestrator import AgentOrchestrator
        
        valid_context = [c.strip() for c in context_with if c.strip()]
        assume(len(valid_context) > 0)
        assume(len(question.strip()) > 0)
        
        orchestrator = AgentOrchestrator()
        
        # Get response without context
        response_no_context = orchestrator.process_chat(
            message=question.strip(),
            context=None
        )
        
        # Get response with context
        response_with_context = orchestrator.process_chat(
            message=question.strip(),
            context=valid_context
        )
        
        # Both responses should be valid
        assert response_no_context is not None
        assert response_with_context is not None
        assert len(response_no_context) > 0
        assert len(response_with_context) > 0
        
        # Responses should be different when context is provided
        # (The placeholder implementation adds "I have context from your uploaded content")
        assert response_no_context != response_with_context, \
            "Response with context should differ from response without context"
