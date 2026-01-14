"""
Authentication service for user management with database persistence.

Uses SQLAlchemy ORM for storing users and sessions in the database.
"""
import bcrypt
from datetime import datetime
from typing import Optional, Tuple

from app.database import db
from app.models.user import User
from app.models.session import Session


class AuthService:
    """Service for handling user authentication operations with database persistence."""
    
    def register(self, email: str, password: str, name: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Register a new user with database persistence.
        
        Args:
            email: User's email address
            password: User's password (will be hashed)
            name: User's display name
            
        Returns:
            Tuple of ({'user': User, 'session': Session}, None) on success,
            or (None, error_message) on failure.
        """
        # Validate inputs
        if not email or not email.strip():
            return None, "Email is required"
        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters"
        if not name or not name.strip():
            return None, "Name is required"
        
        email = email.lower().strip()
        name = name.strip()
        
        # Check if email already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            return None, "An account with this email already exists"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = User(
            email=email,
            name=name,
            password_hash=password_hash,
            is_anonymous=False
        )
        db.session.add(user)
        db.session.commit()
        
        # Create session for the new user
        session = Session.create_for_user(user.id)
        db.session.add(session)
        db.session.commit()
        
        return {'user': user, 'session': session}, None
    
    def login(self, email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of ({'user': User, 'session': Session}, None) on success,
            or (None, error_message) on failure.
        """
        if not email or not password:
            return None, "Email and password are required"
        
        email = email.lower().strip()
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return None, "Invalid email or password"
        
        # Verify password
        if not user.password_hash:
            return None, "Invalid email or password"
        
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None, "Invalid email or password"
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        # Create new session
        session = Session.create_for_user(user.id)
        db.session.add(session)
        db.session.commit()
        
        return {'user': user, 'session': session}, None
    
    def create_anonymous(self) -> dict:
        """
        Create an anonymous user and session.
        
        Returns:
            Dictionary with 'user' and 'session' keys.
        """
        # Create anonymous user
        user = User(
            name='Anonymous User',
            is_anonymous=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Create session for anonymous user
        session = Session.create_for_user(user.id)
        db.session.add(session)
        db.session.commit()
        
        return {'user': user, 'session': session}
    
    def validate_token(self, token: str) -> Optional[User]:
        """
        Validate a session token and return the associated user.
        
        Args:
            token: The session token to validate
            
        Returns:
            User if token is valid and not expired, None otherwise.
        """
        if not token:
            return None
            
        session = Session.query.filter_by(token=token).first()
        if not session:
            return None
        
        if session.is_expired:
            return None
        
        return session.user
    
    def logout(self, token: str) -> bool:
        """
        Invalidate a session (logout).
        
        Args:
            token: The session token to invalidate
            
        Returns:
            True if session was found and deleted, False otherwise.
        """
        if not token:
            return False
            
        session = Session.query.filter_by(token=token).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False
    
    def refresh_session(self, token: str, duration_hours: int = 24) -> Optional[Session]:
        """
        Refresh a session's expiration time.
        
        Args:
            token: The session token to refresh
            duration_hours: How long to extend the session (default 24 hours)
            
        Returns:
            Updated Session if found and not expired, None otherwise.
        """
        if not token:
            return None
            
        session = Session.query.filter_by(token=token).first()
        if not session or session.is_expired:
            return None
        
        session.refresh(duration_hours)
        db.session.commit()
        return session
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return User.query.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        if not email:
            return None
        email = email.lower().strip()
        return User.query.filter_by(email=email).first()
    
    # Legacy method aliases for backward compatibility
    def create_anonymous_session(self) -> Tuple[str, User]:
        """
        Create an anonymous user session (legacy method).
        
        Returns:
            Tuple of (session_token, User).
        """
        result = self.create_anonymous()
        return result['session'].token, result['user']
    
    def create_session(self, user_id: str) -> str:
        """Create a session for an authenticated user (legacy method)."""
        session = Session.create_for_user(user_id)
        db.session.add(session)
        db.session.commit()
        return session.token
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user by session ID (legacy method, alias for validate_token)."""
        return self.validate_token(session_id)
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session (legacy method, alias for logout)."""
        return self.logout(session_id)


# Global auth service instance
auth_service = AuthService()
