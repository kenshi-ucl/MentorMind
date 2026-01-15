"""
Integration tests for content management flows.

Tests the content upload, listing, and deletion flows via the API.
"""
import os
import io
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


@pytest.fixture
def auth_token(client):
    """Create a user and return auth token."""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'name': 'Test User'
    })
    return response.get_json()['token']


@pytest.fixture
def second_auth_token(client):
    """Create a second user and return auth token."""
    response = client.post('/api/auth/register', json={
        'email': 'test2@example.com',
        'password': 'password123',
        'name': 'Test User 2'
    })
    return response.get_json()['token']


class TestContentUpload:
    """Test content upload flow."""
    
    def test_upload_pdf_success(self, client, auth_token):
        """Test successful PDF upload."""
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 test content'), 'test.pdf')
        }
        response = client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 201
        result = response.get_json()
        assert 'contentId' in result
        assert result['filename'] == 'test.pdf'
        assert result['fileType'] == 'pdf'
    
    def test_upload_video_success(self, client, auth_token):
        """Test successful video upload."""
        data = {
            'file': (io.BytesIO(b'fake video content'), 'test.mp4')
        }
        response = client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 201
        result = response.get_json()
        assert result['fileType'] == 'video'
    
    def test_upload_without_auth(self, client):
        """Test upload without authentication fails."""
        data = {
            'file': (io.BytesIO(b'test content'), 'test.pdf')
        }
        response = client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 401
    
    def test_upload_invalid_file_type(self, client, auth_token):
        """Test upload with invalid file type fails."""
        data = {
            'file': (io.BytesIO(b'test content'), 'test.txt')
        }
        response = client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result


class TestContentListing:
    """Test content listing flow."""
    
    def test_list_empty(self, client, auth_token):
        """Test listing with no content."""
        response = client.get(
            '/api/content/list',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'contents' in result
        assert len(result['contents']) == 0
    
    def test_list_with_content(self, client, auth_token):
        """Test listing with uploaded content."""
        # Upload a file first
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 test content'), 'test.pdf')
        }
        client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        # List content
        response = client.get(
            '/api/content/list',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        result = response.get_json()
        assert len(result['contents']) == 1
        assert result['contents'][0]['filename'] == 'test.pdf'
    
    def test_list_without_auth(self, client):
        """Test listing without authentication fails."""
        response = client.get('/api/content/list')
        
        assert response.status_code == 401


class TestContentUserIsolation:
    """Test that users can only see their own content."""
    
    def test_user_isolation(self, client, auth_token, second_auth_token):
        """Test that users can only see their own content."""
        # User 1 uploads a file
        data1 = {
            'file': (io.BytesIO(b'%PDF-1.4 user1 content'), 'user1.pdf')
        }
        client.post(
            '/api/content/upload',
            data=data1,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        # User 2 uploads a file
        data2 = {
            'file': (io.BytesIO(b'%PDF-1.4 user2 content'), 'user2.pdf')
        }
        client.post(
            '/api/content/upload',
            data=data2,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {second_auth_token}'}
        )
        
        # User 1 should only see their file
        response1 = client.get(
            '/api/content/list',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        result1 = response1.get_json()
        assert len(result1['contents']) == 1
        assert result1['contents'][0]['filename'] == 'user1.pdf'
        
        # User 2 should only see their file
        response2 = client.get(
            '/api/content/list',
            headers={'Authorization': f'Bearer {second_auth_token}'}
        )
        result2 = response2.get_json()
        assert len(result2['contents']) == 1
        assert result2['contents'][0]['filename'] == 'user2.pdf'


class TestContentDeletion:
    """Test content deletion flow."""
    
    def test_delete_own_content(self, client, auth_token):
        """Test deleting own content."""
        # Upload a file
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 test content'), 'test.pdf')
        }
        upload_response = client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        content_id = upload_response.get_json()['contentId']
        
        # Delete the file
        response = client.delete(
            f'/api/content/{content_id}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        
        assert response.status_code == 200
        
        # Verify it's gone
        list_response = client.get(
            '/api/content/list',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert len(list_response.get_json()['contents']) == 0
    
    def test_delete_other_user_content(self, client, auth_token, second_auth_token):
        """Test that users cannot delete other users' content."""
        # User 1 uploads a file
        data = {
            'file': (io.BytesIO(b'%PDF-1.4 user1 content'), 'user1.pdf')
        }
        upload_response = client.post(
            '/api/content/upload',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        content_id = upload_response.get_json()['contentId']
        
        # User 2 tries to delete User 1's file
        response = client.delete(
            f'/api/content/{content_id}',
            headers={'Authorization': f'Bearer {second_auth_token}'}
        )
        
        assert response.status_code == 403
        
        # Verify it still exists for User 1
        list_response = client.get(
            '/api/content/list',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert len(list_response.get_json()['contents']) == 1
