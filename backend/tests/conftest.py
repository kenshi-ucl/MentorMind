"""Shared test fixtures for pytest."""
import os
import pytest
from app import create_app
from app.database import db


@pytest.fixture(scope='function')
def app():
    """Create application for testing with in-memory SQLite database."""
    # Set test database URL to in-memory SQLite
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        # Clean up after test
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provide a database session for tests."""
    with app.app_context():
        yield db.session
        db.session.rollback()
