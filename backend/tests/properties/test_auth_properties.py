"""Property-based tests for authentication.

Feature: mentormind-ai-tutor

NOTE: These tests have been superseded by test_database_auth_properties.py
which provides comprehensive property-based testing for the database-backed
authentication service. These tests are kept for backward compatibility
and test the same properties within the Flask app context.
"""
import os
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

# Set test database before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database import db
from app.services.auth_service import AuthService
from app.models.user import User
from app.models.session import Session


# Simplified strategies for faster test execution
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


class TestAuthProperties:
    """Property-based tests for authentication service."""
    
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        name=name_strategy
    )
    def test_property_1_registration_login_round_trip(self, email, password, name):
        """
        Property 1: User Registration and Login Round-Trip
        
        For any valid user registration data (email, password, name), 
        registering a user and then logging in with those credentials 
        should return the same user profile with matching email and name.
        
        Validates: Requirements 1.3, 1.4
        """
        # Skip if name is only whitespace
        assume(name.strip())
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            # Clean up any existing data
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            # Create fresh auth service for each test
            auth = AuthService()
            
            # Register user
            result, reg_error = auth.register(email, password, name)
            
            # Registration should succeed
            assert reg_error is None, f"Registration failed: {reg_error}"
            assert result is not None
            registered_user = result['user']
            
            # Login with same credentials
            login_result, login_error = auth.login(email, password)
            
            # Login should succeed
            assert login_error is None, f"Login failed: {login_error}"
            assert login_result is not None
            logged_in_user = login_result['user']
            
            # User profile should match
            assert logged_in_user.email == registered_user.email
            assert logged_in_user.name == registered_user.name
            assert logged_in_user.id == registered_user.id
            assert logged_in_user.is_anonymous == False
            
            db.session.remove()
            db.drop_all()

    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        email=email_strategy,
        password=password_strategy,
        name=name_strategy,
        wrong_password=password_strategy
    )
    def test_property_2_invalid_credentials_rejection(self, email, password, name, wrong_password):
        """
        Property 2: Invalid Credentials Rejection
        
        For any credential combination where the email does not exist in the system 
        OR the password does not match the stored hash, the authentication attempt 
        should fail and return an error response.
        
        Validates: Requirements 1.5
        """
        # Skip if name is only whitespace
        assume(name.strip())
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            # Clean up any existing data
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            auth = AuthService()
            
            # Test 1: Login with non-existent email should fail
            result, error = auth.login(email, password)
            assert result is None
            assert error is not None
            assert "Invalid email or password" in error
            
            # Register a user
            reg_result, reg_error = auth.register(email, password, name)
            assert reg_error is None
            
            # Test 2: Login with wrong password should fail (if passwords differ)
            if wrong_password != password:
                result, error = auth.login(email, wrong_password)
                assert result is None
                assert error is not None
                assert "Invalid email or password" in error
            
            # Test 3: Login with non-existent email after registration should still fail
            fake_email = "nonexistent_" + email
            result, error = auth.login(fake_email, password)
            assert result is None
            assert error is not None
            
            db.session.remove()
            db.drop_all()
