"""
Property-based tests for database authentication.

Feature: database-integration
Tests the SQLAlchemy-based AuthService for user persistence and authentication.
"""
import os
import uuid
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta

# Set test database before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database import db
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.session import Session


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


class TestUserPersistenceRoundTrip:
    """
    Property 1: User Persistence Round-Trip
    
    For any valid user registration data (email, password, name), registering 
    the user and then retrieving by email SHALL return the same user data 
    (excluding password which is hashed).
    
    **Validates: Requirements 2.1, 2.3, 2.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        name=name_strategy
    )
    def test_property_1_user_persistence_round_trip(self, email, password, name):
        """
        Property 1: User Persistence Round-Trip
        
        For any valid user registration data (email, password, name), registering 
        the user and then retrieving by email SHALL return the same user data.
        
        **Validates: Requirements 2.1, 2.3, 2.5**
        """
        assume(name.strip())
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            result, error = auth.register(email, password, name)
            
            assert error is None, f"Registration failed: {error}"
            assert result is not None
            assert 'user' in result
            assert 'session' in result
            
            registered_user = result['user']
            retrieved_user = auth.get_user_by_email(email)
            
            assert retrieved_user is not None
            assert retrieved_user.id == registered_user.id
            assert retrieved_user.email == email.lower().strip()
            assert retrieved_user.name == name.strip()
            assert retrieved_user.is_anonymous == False
            assert retrieved_user.password_hash is not None
            assert retrieved_user.password_hash != password
            
            user_by_id = auth.get_user_by_id(registered_user.id)
            assert user_by_id is not None
            assert user_by_id.id == registered_user.id
            
            db.session.remove()
            db.drop_all()

    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(True))
    def test_property_1_anonymous_user_persistence(self, _):
        """
        Property 1 (extension): Anonymous User Persistence
        **Validates: Requirements 2.3**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            result = auth.create_anonymous()
            
            assert result is not None
            assert 'user' in result
            assert 'session' in result
            
            anon_user = result['user']
            assert anon_user.is_anonymous == True
            assert anon_user.email is None
            
            retrieved_user = auth.get_user_by_id(anon_user.id)
            assert retrieved_user is not None
            assert retrieved_user.id == anon_user.id
            assert retrieved_user.is_anonymous == True
            
            db.session.remove()
            db.drop_all()


class TestAuthenticationCorrectness:
    """
    Property 2: Authentication Correctness
    
    For any registered user with email and password, logging in with correct 
    credentials SHALL succeed and return a valid session, while logging in 
    with incorrect credentials SHALL fail.
    
    **Validates: Requirements 2.2**
    """
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        name=name_strategy,
        wrong_password=password_strategy
    )
    def test_property_2_correct_credentials_succeed(self, email, password, name, wrong_password):
        """
        Property 2: Authentication Correctness - Correct credentials succeed
        
        For any registered user, logging in with the correct password SHALL 
        succeed and return a valid session.
        
        **Validates: Requirements 2.2**
        """
        assume(name.strip())
        assume(password != wrong_password)  # Ensure wrong password is different
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register user
            reg_result, reg_error = auth.register(email, password, name)
            assert reg_error is None, f"Registration failed: {reg_error}"
            
            # Login with correct credentials should succeed
            login_result, login_error = auth.login(email, password)
            assert login_error is None, f"Login with correct credentials failed: {login_error}"
            assert login_result is not None
            assert 'user' in login_result
            assert 'session' in login_result
            assert login_result['user'].email == email.lower().strip()
            assert login_result['session'].token is not None
            
            # Login with wrong password should fail
            wrong_result, wrong_error = auth.login(email, wrong_password)
            assert wrong_result is None, "Login with wrong password should fail"
            assert wrong_error is not None
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        wrong_email=email_strategy
    )
    def test_property_2_wrong_email_fails(self, email, password, wrong_email):
        """
        Property 2: Authentication Correctness - Wrong email fails
        
        For any registered user, logging in with a non-existent email SHALL fail.
        
        **Validates: Requirements 2.2**
        """
        assume(email != wrong_email)  # Ensure wrong email is different
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register user with original email
            reg_result, reg_error = auth.register(email, password, "Test User")
            assert reg_error is None, f"Registration failed: {reg_error}"
            
            # Login with wrong email should fail
            wrong_result, wrong_error = auth.login(wrong_email, password)
            assert wrong_result is None, "Login with wrong email should fail"
            assert wrong_error is not None
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy
    )
    def test_property_2_login_creates_valid_session(self, email, password):
        """
        Property 2: Authentication Correctness - Login creates valid session
        
        For any successful login, the returned session token SHALL be valid 
        for authentication.
        
        **Validates: Requirements 2.2**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register user
            reg_result, reg_error = auth.register(email, password, "Test User")
            assert reg_error is None, f"Registration failed: {reg_error}"
            
            # Login
            login_result, login_error = auth.login(email, password)
            assert login_error is None, f"Login failed: {login_error}"
            
            # Validate the session token
            session_token = login_result['session'].token
            validated_user = auth.validate_token(session_token)
            
            assert validated_user is not None, "Session token should be valid"
            assert validated_user.id == login_result['user'].id
            assert validated_user.email == email.lower().strip()
            
            db.session.remove()
            db.drop_all()


class TestSessionLifecycleValidity:
    """
    Property 3: Session Lifecycle Validity
    
    For any authenticated user session, the token SHALL be valid until expiration, 
    and SHALL be invalid after expiration or logout.
    
    **Validates: Requirements 3.1, 3.3, 3.4**
    """
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy
    )
    def test_property_3_session_valid_until_expiration(self, email, password):
        """
        Property 3: Session Lifecycle - Token valid until expiration
        
        For any authenticated user, the session token SHALL be valid 
        immediately after creation.
        
        **Validates: Requirements 3.1, 3.3**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register and login
            reg_result, _ = auth.register(email, password, "Test User")
            assert reg_result is not None
            
            login_result, _ = auth.login(email, password)
            assert login_result is not None
            
            session_token = login_result['session'].token
            
            # Token should be valid immediately after creation
            validated_user = auth.validate_token(session_token)
            assert validated_user is not None, "Session should be valid immediately after creation"
            assert validated_user.id == login_result['user'].id
            
            # Session should not be expired
            session = Session.query.filter_by(token=session_token).first()
            assert session is not None
            assert session.is_expired == False
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy
    )
    def test_property_3_session_invalid_after_logout(self, email, password):
        """
        Property 3: Session Lifecycle - Token invalid after logout
        
        For any authenticated user, the session token SHALL be invalid 
        after logout.
        
        **Validates: Requirements 3.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register and login
            reg_result, _ = auth.register(email, password, "Test User")
            assert reg_result is not None
            
            login_result, _ = auth.login(email, password)
            assert login_result is not None
            
            session_token = login_result['session'].token
            
            # Token should be valid before logout
            validated_user = auth.validate_token(session_token)
            assert validated_user is not None, "Session should be valid before logout"
            
            # Logout
            logout_success = auth.logout(session_token)
            assert logout_success == True, "Logout should succeed"
            
            # Token should be invalid after logout
            validated_user_after = auth.validate_token(session_token)
            assert validated_user_after is None, "Session should be invalid after logout"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy
    )
    def test_property_3_session_invalid_after_expiration(self, email, password):
        """
        Property 3: Session Lifecycle - Token invalid after expiration
        
        For any authenticated user, the session token SHALL be invalid 
        after expiration.
        
        **Validates: Requirements 3.3, 3.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register user
            reg_result, _ = auth.register(email, password, "Test User")
            assert reg_result is not None
            
            user_id = reg_result['user'].id
            
            # Create a session that's already expired (negative duration)
            expired_session = Session(
                user_id=user_id,
                token=str(uuid.uuid4()),
                expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
            )
            db.session.add(expired_session)
            db.session.commit()
            
            # Token should be invalid because it's expired
            validated_user = auth.validate_token(expired_session.token)
            assert validated_user is None, "Expired session should be invalid"
            
            # Verify the session is marked as expired
            assert expired_session.is_expired == True
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy
    )
    def test_property_3_multiple_sessions_independent(self, email, password):
        """
        Property 3: Session Lifecycle - Multiple sessions are independent
        
        For any user with multiple sessions, invalidating one session 
        SHALL NOT affect other sessions.
        
        **Validates: Requirements 3.1, 3.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Register user
            reg_result, _ = auth.register(email, password, "Test User")
            assert reg_result is not None
            
            # Login twice to create two sessions
            login_result1, _ = auth.login(email, password)
            login_result2, _ = auth.login(email, password)
            
            assert login_result1 is not None
            assert login_result2 is not None
            
            token1 = login_result1['session'].token
            token2 = login_result2['session'].token
            
            # Both tokens should be valid
            assert auth.validate_token(token1) is not None
            assert auth.validate_token(token2) is not None
            
            # Logout from first session
            auth.logout(token1)
            
            # First token should be invalid, second should still be valid
            assert auth.validate_token(token1) is None, "First session should be invalid after logout"
            assert auth.validate_token(token2) is not None, "Second session should still be valid"
            
            db.session.remove()
            db.drop_all()
