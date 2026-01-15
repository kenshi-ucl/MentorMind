"""
Integration tests for authentication flows.

Tests the register, login, anonymous, and logout flows via the API.
"""
import os
import pytest

# Set test database before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database import db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestRegisterFlow:
    """Test user registration flow."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'user' in data
        assert 'token' in data
        assert data['user']['email'] == 'test@example.com'
        assert data['user']['name'] == 'Test User'
        assert data['user']['is_anonymous'] == False
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        # First registration
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        
        # Second registration with same email
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password456',
            'name': 'Another User'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'error' in data
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields fails."""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400


class TestLoginFlow:
    """Test user login flow."""
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register first
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        
        # Login
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert 'token' in data
        assert data['user']['email'] == 'test@example.com'
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password fails."""
        # Register first
        client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        
        # Login with wrong password
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 401


class TestAnonymousFlow:
    """Test anonymous session flow."""
    
    def test_anonymous_session_creation(self, client):
        """Test anonymous session creation."""
        response = client.post('/api/auth/anonymous')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert 'sessionId' in data
        assert data['isAnonymous'] == True
        assert 'user' in data
        assert data['user']['is_anonymous'] == True


class TestAuthenticatedRoutes:
    """Test authenticated route access."""
    
    def test_get_current_user_with_valid_token(self, client):
        """Test getting current user with valid token."""
        # Register and get token
        reg_response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        token = reg_response.get_json()['token']
        
        # Get current user
        response = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['email'] == 'test@example.com'
    
    def test_get_current_user_without_token(self, client):
        """Test getting current user without token returns 401."""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_get_current_user_with_invalid_token(self, client):
        """Test getting current user with invalid token returns 401."""
        response = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalid-token-12345'
        })
        
        assert response.status_code == 401


class TestLogoutFlow:
    """Test logout flow."""
    
    def test_logout_success(self, client):
        """Test successful logout."""
        # Register and get token
        reg_response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        token = reg_response.get_json()['token']
        
        # Logout
        response = client.post('/api/auth/logout', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        
        # Verify token is now invalid
        me_response = client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert me_response.status_code == 401
    
    def test_logout_without_token(self, client):
        """Test logout without token returns 401."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401
