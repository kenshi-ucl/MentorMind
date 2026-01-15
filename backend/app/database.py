"""
Database configuration module for MentorMind.

Configures SQLAlchemy with Flask, supporting both SQLite (default) and MySQL.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


db = SQLAlchemy(model_class=Base)


def get_database_url():
    """
    Get database URL from environment or use SQLite default.
    
    Returns:
        str: Database connection URL
    """
    # Check for DATABASE_URL environment variable (supports MySQL)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        return database_url
    
    # Default to SQLite at backend/data/mentormind.db
    # Get the backend directory path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(backend_dir, 'data')
    db_path = os.path.join(data_dir, 'mentormind.db')
    
    return f'sqlite:///{db_path}'


def init_db(app):
    """
    Initialize database with Flask app.
    
    Args:
        app: Flask application instance
    """
    database_url = get_database_url()
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Connection pooling settings for production
    if not database_url.startswith('sqlite'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
    
    db.init_app(app)
    
    # Create data directory if using SQLite
    if database_url.startswith('sqlite'):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(backend_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
    
    # Import models before creating tables so SQLAlchemy knows about them
    # This must happen after db.init_app() but before db.create_all()
    from app.models import User, Session, Content, QuizResult, Conversation, Message
    from app.models import (Friend, FriendRequest, DirectChat, DirectMessage, 
                           GroupMessage, GroupLearning, GroupMember, Call, 
                           CallParticipant, UserPresence)
    
    # Create all tables
    with app.app_context():
        db.create_all()
