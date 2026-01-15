"""
Property-based tests for database content persistence.

Feature: database-integration
Tests the SQLAlchemy-based ContentService for content persistence and user isolation.
"""
import os
import tempfile
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Set test database before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database import db
from app.services.content_service import ContentService
from app.services.auth_service import AuthService
from app.models.content import Content
from app.models.user import User
from app.models.session import Session


# Strategies for generating test data
filename_strategy = st.builds(
    lambda name, ext: f"{name}{ext}",
    name=st.text(min_size=1, max_size=15, alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-'),
    ext=st.sampled_from(['.pdf', '.mp4', '.avi', '.mov', '.mkv', '.webm'])
)

file_data_strategy = st.binary(min_size=10, max_size=1000)

email_strategy = st.from_regex(r'[a-z]{3,8}@[a-z]{3,6}\.(com|org|net)', fullmatch=True)
password_strategy = st.text(min_size=6, max_size=12, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
name_strategy = st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')


def get_test_app():
    """Create a fresh test application with in-memory database."""
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


class TestContentUserIsolation:
    """
    Property 4: Content User Isolation
    
    For any two different users A and B, content uploaded by user A SHALL NOT 
    be visible when listing content for user B, and vice versa.
    
    **Validates: Requirements 4.3**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email_a=email_strategy,
        email_b=email_strategy,
        password=password_strategy,
        filename_a=filename_strategy,
        filename_b=filename_strategy,
        file_data_a=file_data_strategy,
        file_data_b=file_data_strategy
    )
    def test_property_4_content_user_isolation(self, email_a, email_b, password, 
                                                filename_a, filename_b,
                                                file_data_a, file_data_b):
        """
        Property 4: Content User Isolation
        
        For any two different users A and B, content uploaded by user A SHALL NOT 
        be visible when listing content for user B, and vice versa.
        
        **Validates: Requirements 4.3**
        """
        # Ensure users have different emails
        assume(email_a != email_b)
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            # Clean up any existing data
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register two users
                result_a, error_a = auth.register(email_a, password, "User A")
                assert error_a is None, f"Failed to register user A: {error_a}"
                user_a = result_a['user']
                
                result_b, error_b = auth.register(email_b, password, "User B")
                assert error_b is None, f"Failed to register user B: {error_b}"
                user_b = result_b['user']
                
                # Upload content for user A
                content_a, error = content_service.upload_content(
                    user_id=user_a.id,
                    filename=filename_a,
                    file_data=file_data_a
                )
                assert error is None, f"Failed to upload content for user A: {error}"
                
                # Upload content for user B
                content_b, error = content_service.upload_content(
                    user_id=user_b.id,
                    filename=filename_b,
                    file_data=file_data_b
                )
                assert error is None, f"Failed to upload content for user B: {error}"
                
                # Get content list for user A
                user_a_contents = content_service.get_user_content(user_a.id)
                user_a_content_ids = [c.id for c in user_a_contents]
                
                # Get content list for user B
                user_b_contents = content_service.get_user_content(user_b.id)
                user_b_content_ids = [c.id for c in user_b_contents]
                
                # User A should only see their own content
                assert content_a.id in user_a_content_ids, "User A should see their own content"
                assert content_b.id not in user_a_content_ids, "User A should NOT see user B's content"
                
                # User B should only see their own content
                assert content_b.id in user_b_content_ids, "User B should see their own content"
                assert content_a.id not in user_b_content_ids, "User B should NOT see user A's content"
                
                # Verify get_content with user_id filter
                # User A should not be able to get user B's content
                content_b_for_a = content_service.get_content(content_b.id, user_a.id)
                assert content_b_for_a is None, "User A should not access user B's content via get_content"
                
                # User B should not be able to get user A's content
                content_a_for_b = content_service.get_content(content_a.id, user_b.id)
                assert content_a_for_b is None, "User B should not access user A's content via get_content"
                
                # Users should be able to get their own content
                content_a_for_a = content_service.get_content(content_a.id, user_a.id)
                assert content_a_for_a is not None, "User A should access their own content"
                assert content_a_for_a.id == content_a.id
                
                content_b_for_b = content_service.get_content(content_b.id, user_b.id)
                assert content_b_for_b is not None, "User B should access their own content"
                assert content_b_for_b.id == content_b.id
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email_a=email_strategy,
        email_b=email_strategy,
        password=password_strategy,
        filename=filename_strategy,
        file_data=file_data_strategy
    )
    def test_property_4_delete_isolation(self, email_a, email_b, password, filename, file_data):
        """
        Property 4 (extension): Delete Isolation
        
        User A should not be able to delete user B's content.
        
        **Validates: Requirements 4.3**
        """
        assume(email_a != email_b)
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register two users
                result_a, _ = auth.register(email_a, password, "User A")
                user_a = result_a['user']
                
                result_b, _ = auth.register(email_b, password, "User B")
                user_b = result_b['user']
                
                # Upload content for user B
                content_b, _ = content_service.upload_content(
                    user_id=user_b.id,
                    filename=filename,
                    file_data=file_data
                )
                
                # User A tries to delete user B's content
                success, error = content_service.delete_content(content_b.id, user_a.id)
                
                # Should fail
                assert success is False, "User A should not be able to delete user B's content"
                assert "not authorized" in error.lower(), f"Error should mention authorization: {error}"
                
                # Content should still exist
                content_still_exists = content_service.get_content(content_b.id, user_b.id)
                assert content_still_exists is not None, "Content should still exist after failed delete"
            
            db.session.remove()
            db.drop_all()



class TestContentPersistenceRoundTrip:
    """
    Property 5: Content Persistence Round-Trip
    
    For any uploaded content with metadata, saving and then retrieving the content 
    SHALL return the same metadata (filename, content_type, title, summary, key_points).
    
    **Validates: Requirements 4.1, 4.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filename=filename_strategy,
        file_data=file_data_strategy
    )
    def test_property_5_content_persistence_round_trip(self, email, password, filename, file_data):
        """
        Property 5: Content Persistence Round-Trip
        
        For any uploaded content with metadata, saving and then retrieving the content 
        SHALL return the same metadata (filename, content_type).
        
        **Validates: Requirements 4.1, 4.5**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register user
                result, error = auth.register(email, password, "Test User")
                assert error is None, f"Failed to register user: {error}"
                user = result['user']
                
                # Upload content
                content, error = content_service.upload_content(
                    user_id=user.id,
                    filename=filename,
                    file_data=file_data
                )
                assert error is None, f"Failed to upload content: {error}"
                assert content is not None
                
                original_id = content.id
                original_filename = content.filename
                original_content_type = content.content_type
                original_file_size = content.file_size
                
                # Retrieve content by ID
                retrieved = content_service.get_content(original_id)
                
                # Verify round-trip preserves data
                assert retrieved is not None, "Content should be retrievable"
                assert retrieved.id == original_id, "ID should match"
                assert retrieved.filename == original_filename, "Filename should match"
                assert retrieved.content_type == original_content_type, "Content type should match"
                assert retrieved.file_size == original_file_size, "File size should match"
                assert retrieved.user_id == user.id, "User ID should match"
                
                # Verify file exists on disk
                assert os.path.exists(retrieved.file_path), "File should exist on disk"
                
                # Verify file content matches
                with open(retrieved.file_path, 'rb') as f:
                    saved_data = f.read()
                assert saved_data == file_data, "File content should match original"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filename=filename_strategy,
        file_data=file_data_strategy,
        title=st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
        summary=st.text(min_size=1, max_size=200, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,'),
        key_points=st.lists(
            st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '),
            min_size=1,
            max_size=5
        ),
        topics=st.lists(
            st.text(min_size=1, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            min_size=0,
            max_size=3
        )
    )
    def test_property_5_metadata_persistence_round_trip(self, email, password, filename, file_data,
                                                         title, summary, key_points, topics):
        """
        Property 5 (extension): Metadata Persistence Round-Trip
        
        For any content with updated metadata (title, summary, key_points, topics),
        the metadata SHALL be preserved after update and retrieval.
        
        **Validates: Requirements 4.5**
        """
        assume(title.strip())
        assume(summary.strip())
        assume(all(kp.strip() for kp in key_points))
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register user
                result, _ = auth.register(email, password, "Test User")
                user = result['user']
                
                # Upload content
                content, _ = content_service.upload_content(
                    user_id=user.id,
                    filename=filename,
                    file_data=file_data
                )
                
                # Update metadata
                updated = content_service.update_content_metadata(
                    content_id=content.id,
                    title=title.strip(),
                    summary=summary.strip(),
                    key_points=[kp.strip() for kp in key_points],
                    topics=[t.strip() for t in topics if t.strip()]
                )
                
                assert updated is not None, "Update should succeed"
                
                # Retrieve content
                retrieved = content_service.get_content(content.id)
                
                # Verify metadata round-trip
                assert retrieved.title == title.strip(), "Title should match"
                assert retrieved.summary == summary.strip(), "Summary should match"
                assert retrieved.key_points == [kp.strip() for kp in key_points], "Key points should match"
                assert retrieved.topics == [t.strip() for t in topics if t.strip()], "Topics should match"
                assert retrieved.processing_status == 'complete', "Processing status should be complete"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filenames=st.lists(filename_strategy, min_size=2, max_size=5, unique=True),
        file_data=file_data_strategy
    )
    def test_property_5_multiple_content_persistence(self, email, password, filenames, file_data):
        """
        Property 5 (extension): Multiple Content Persistence
        
        For any user with multiple uploaded content items, all items SHALL be 
        retrievable and maintain their individual metadata.
        
        **Validates: Requirements 4.1**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register user
                result, _ = auth.register(email, password, "Test User")
                user = result['user']
                
                # Upload multiple content items
                uploaded_contents = []
                for fname in filenames:
                    content, error = content_service.upload_content(
                        user_id=user.id,
                        filename=fname,
                        file_data=file_data
                    )
                    assert error is None, f"Failed to upload {fname}: {error}"
                    uploaded_contents.append(content)
                
                # Retrieve all content for user
                user_contents = content_service.get_user_content(user.id)
                
                # Verify all content is retrievable
                assert len(user_contents) == len(filenames), "All content should be retrievable"
                
                retrieved_filenames = {c.filename for c in user_contents}
                original_filenames = set(filenames)
                
                assert retrieved_filenames == original_filenames, "All filenames should match"
                
                # Verify each content item individually
                for original in uploaded_contents:
                    retrieved = content_service.get_content(original.id)
                    assert retrieved is not None, f"Content {original.id} should be retrievable"
                    assert retrieved.filename == original.filename
                    assert retrieved.content_type == original.content_type
            
            db.session.remove()
            db.drop_all()


class TestContentDeletionCompleteness:
    """
    Property 6: Content Deletion Completeness
    
    For any deleted content, both the database record AND the physical file 
    SHALL be removed.
    
    **Validates: Requirements 4.4**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filename=filename_strategy,
        file_data=file_data_strategy
    )
    def test_property_6_content_deletion_completeness(self, email, password, filename, file_data):
        """
        Property 6: Content Deletion Completeness
        
        For any deleted content, both the database record AND the physical file 
        SHALL be removed.
        
        **Validates: Requirements 4.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register user
                result, error = auth.register(email, password, "Test User")
                assert error is None, f"Failed to register user: {error}"
                user = result['user']
                
                # Upload content
                content, error = content_service.upload_content(
                    user_id=user.id,
                    filename=filename,
                    file_data=file_data
                )
                assert error is None, f"Failed to upload content: {error}"
                assert content is not None
                
                content_id = content.id
                file_path = content.file_path
                
                # Verify content exists before deletion
                assert Content.query.get(content_id) is not None, "Content should exist in database"
                assert os.path.exists(file_path), "File should exist on disk"
                
                # Delete content
                success, error = content_service.delete_content(content_id, user.id)
                assert success is True, f"Delete should succeed: {error}"
                assert error is None, "No error should be returned"
                
                # Verify database record is removed
                deleted_content = Content.query.get(content_id)
                assert deleted_content is None, "Database record should be removed after deletion"
                
                # Verify physical file is removed
                assert not os.path.exists(file_path), "Physical file should be removed after deletion"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filenames=st.lists(filename_strategy, min_size=2, max_size=4, unique=True),
        file_data=file_data_strategy
    )
    def test_property_6_selective_deletion(self, email, password, filenames, file_data):
        """
        Property 6 (extension): Selective Deletion
        
        When one content item is deleted, other content items for the same user
        SHALL remain intact (both database records and files).
        
        **Validates: Requirements 4.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register user
                result, _ = auth.register(email, password, "Test User")
                user = result['user']
                
                # Upload multiple content items
                uploaded_contents = []
                for fname in filenames:
                    content, error = content_service.upload_content(
                        user_id=user.id,
                        filename=fname,
                        file_data=file_data
                    )
                    assert error is None, f"Failed to upload {fname}: {error}"
                    uploaded_contents.append(content)
                
                # Delete the first content item
                content_to_delete = uploaded_contents[0]
                remaining_contents = uploaded_contents[1:]
                
                deleted_id = content_to_delete.id
                deleted_file_path = content_to_delete.file_path
                
                success, error = content_service.delete_content(deleted_id, user.id)
                assert success is True, f"Delete should succeed: {error}"
                
                # Verify deleted content is gone
                assert Content.query.get(deleted_id) is None, "Deleted content should be removed from database"
                assert not os.path.exists(deleted_file_path), "Deleted file should be removed from disk"
                
                # Verify remaining content is intact
                for remaining in remaining_contents:
                    # Database record should exist
                    db_record = Content.query.get(remaining.id)
                    assert db_record is not None, f"Content {remaining.id} should still exist in database"
                    assert db_record.filename == remaining.filename, "Filename should be preserved"
                    
                    # File should exist
                    assert os.path.exists(remaining.file_path), f"File {remaining.file_path} should still exist"
                
                # Verify user content list is correct
                user_contents = content_service.get_user_content(user.id)
                assert len(user_contents) == len(remaining_contents), "User should have correct number of content items"
                
                remaining_ids = {c.id for c in remaining_contents}
                retrieved_ids = {c.id for c in user_contents}
                assert remaining_ids == retrieved_ids, "Remaining content IDs should match"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filename=filename_strategy,
        file_data=file_data_strategy
    )
    def test_property_6_double_deletion_handling(self, email, password, filename, file_data):
        """
        Property 6 (extension): Double Deletion Handling
        
        Attempting to delete already-deleted content SHALL fail gracefully
        without causing errors.
        
        **Validates: Requirements 4.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                auth = AuthService()
                content_service = ContentService(upload_dir=temp_dir)
                
                # Register user
                result, _ = auth.register(email, password, "Test User")
                user = result['user']
                
                # Upload content
                content, _ = content_service.upload_content(
                    user_id=user.id,
                    filename=filename,
                    file_data=file_data
                )
                
                content_id = content.id
                
                # First deletion should succeed
                success1, error1 = content_service.delete_content(content_id, user.id)
                assert success1 is True, f"First delete should succeed: {error1}"
                
                # Second deletion should fail gracefully
                success2, error2 = content_service.delete_content(content_id, user.id)
                assert success2 is False, "Second delete should fail"
                assert error2 is not None, "Error message should be provided"
                assert "not found" in error2.lower(), f"Error should indicate content not found: {error2}"
            
            db.session.remove()
            db.drop_all()
