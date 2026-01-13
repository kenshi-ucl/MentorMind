"""Shared test fixtures for pytest."""
import pytest
from app import create_app
from app.services.auth_service import auth_service


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_auth_service():
    """Clean auth service before each test."""
    auth_service.clear_all()
    yield
    auth_service.clear_all()
