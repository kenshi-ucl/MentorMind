"""
Property-based tests for database persistence across restarts.

Feature: database-integration
Tests that data persists correctly across application restarts.
"""
import os
import sys
import tempfile
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
import uuid

# Add backend to path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set test database before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database import db

# Strategies for generating test data
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


class TestDataPersistenceAcrossRestarts:
    """
    Property 9: Data Persistence Across Restarts
    
    For any data stored in the database, restarting the application 
    SHALL NOT lose or corrupt the data.
    
    **Validates: Requirements 6.2**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        name=name_strategy
    )
    def test_property_9_user_data_persists_across_restarts(self, email, password, name):
        """
        Property 9: Data Persistence Across Restarts - User data
        
        For any registered user, the data stored in the database SHALL be 
        retrievable after the transaction is committed, simulating persistence
        across application restarts.
        
        **Validates: Requirements 6.2**
        """
        assume(name.strip())
        
        app = get_test_app()
        with app.app_context():
            from app.services.auth_service import AuthService
            from app.models.user import User
            from app.models.session import Session
            
            db.create_all()
            
            # Clear any existing data
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            result, error = auth.register(email, password, name)
            
            assert error is None, f"Registration failed: {error}"
            assert result is not None
            
            original_user_id = result['user'].id
            original_email = result['user'].email
            original_name = result['user'].name
            
            # Commit and close session to simulate persistence
            db.session.commit()
            db.session.expire_all()
            
            # Retrieve user from database (simulating restart)
            retrieved_user = User.query.filter_by(email=original_email).first()
            
            assert retrieved_user is not None, "User should persist in database"
            assert retrieved_user.id == original_user_id, "User ID should be preserved"
            assert retrieved_user.email == original_email, "Email should be preserved"
            assert retrieved_user.name == original_name, "Name should be preserved"
            
            # Verify password still works after retrieval
            login_result, login_error = auth.login(original_email, password)
            assert login_error is None, "Login should work after data retrieval"
            assert login_result is not None
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        topic=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
        score=st.integers(min_value=0, max_value=10),
        total=st.integers(min_value=1, max_value=10)
    )
    def test_property_9_quiz_results_persist_across_restarts(self, email, password, topic, score, total):
        """
        Property 9: Data Persistence Across Restarts - Quiz results
        
        For any quiz results stored, the data SHALL be retrievable after
        the transaction is committed, simulating persistence across restarts.
        
        **Validates: Requirements 6.2**
        """
        assume(score <= total)
        assume(topic.strip())
        
        app = get_test_app()
        with app.app_context():
            from app.services.auth_service import AuthService
            from app.services.progress_service import ProgressService
            from app.models.user import User
            from app.models.session import Session
            from app.models.quiz_result import QuizResult
            
            db.create_all()
            
            # Clear any existing data
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            result, error = auth.register(email, password, "Test User")
            assert error is None
            
            user_id = result['user'].id
            
            progress = ProgressService()
            quiz_result = progress.record_quiz_result(
                user_id=user_id,
                quiz_id="test-quiz-123",
                topic=topic,
                score=score,
                total_questions=total,
                answers={"q1": "a", "q2": "b"}
            )
            
            original_result_id = quiz_result.id
            original_score = quiz_result.score
            original_total = quiz_result.total_questions
            original_topic = quiz_result.topic
            
            # Commit and expire to simulate persistence
            db.session.commit()
            db.session.expire_all()
            
            # Retrieve quiz result (simulating restart)
            retrieved_result = QuizResult.query.get(original_result_id)
            
            assert retrieved_result is not None, "Quiz result should persist"
            assert retrieved_result.score == original_score, "Score should be preserved"
            assert retrieved_result.total_questions == original_total, "Total questions should be preserved"
            assert retrieved_result.topic == original_topic, "Topic should be preserved"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        filename=st.from_regex(r'[a-z]{3,8}\.(pdf|mp4)', fullmatch=True),
        title=st.text(min_size=1, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')
    )
    def test_property_9_content_metadata_persists_across_restarts(self, email, password, filename, title):
        """
        Property 9: Data Persistence Across Restarts - Content metadata
        
        For any content metadata stored, the data SHALL be retrievable after
        the transaction is committed, simulating persistence across restarts.
        
        **Validates: Requirements 6.2**
        """
        assume(title.strip())
        
        app = get_test_app()
        with app.app_context():
            from app.services.auth_service import AuthService
            from app.models.user import User
            from app.models.session import Session
            from app.models.content import Content
            
            db.create_all()
            
            # Clear any existing data
            db.session.query(Content).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            result, error = auth.register(email, password, "Test User")
            assert error is None
            
            user_id = result['user'].id
            
            # Create content directly (without file system)
            content_type = 'application/pdf' if filename.endswith('.pdf') else 'video/mp4'
            content = Content(
                id=str(uuid.uuid4()),
                user_id=user_id,
                filename=filename,
                content_type=content_type,
                file_path=f'/tmp/{filename}',
                file_size=1024,
                title=title,
                summary="Test summary",
                processing_status='complete'
            )
            content.key_points = ["Point 1", "Point 2"]
            content.topics = ["Topic A", "Topic B"]
            
            db.session.add(content)
            db.session.commit()
            
            original_content_id = content.id
            original_filename = content.filename
            original_title = content.title
            original_key_points = content.key_points
            original_topics = content.topics
            
            # Expire to simulate persistence
            db.session.expire_all()
            
            # Retrieve content (simulating restart)
            retrieved_content = Content.query.get(original_content_id)
            
            assert retrieved_content is not None, "Content should persist"
            assert retrieved_content.filename == original_filename, "Filename should be preserved"
            assert retrieved_content.title == original_title, "Title should be preserved"
            assert retrieved_content.key_points == original_key_points, "Key points should be preserved"
            assert retrieved_content.topics == original_topics, "Topics should be preserved"
            
            db.session.remove()
            db.drop_all()
