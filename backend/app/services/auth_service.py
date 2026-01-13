"""Authentication service for user management."""
import uuid
import bcrypt
from datetime import datetime
from typing import Optional, Tuple
from app.models.user import User


class AuthService:
    """Service for handling user authentication operations."""
    
    def __init__(self):
        # In-memory user storage (would be replaced with database in production)
        self._users: dict[str, User] = {}
        self._email_index: dict[str, str] = {}  # email -> user_id mapping
        self._sessions: dict[str, str] = {}  # session_id -> user_id mapping
    
    def register(self, email: str, password: str, name: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user.
        
        Returns:
            Tuple of (User, None) on success, or (None, error_message) on failure.
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
        if email in self._email_index:
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
        
        # Store user
        self._users[user.id] = user
        self._email_index[email] = user.id
        
        return user, None
    
    def login(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user with email and password.
        
        Returns:
            Tuple of (User, None) on success, or (None, error_message) on failure.
        """
        if not email or not password:
            return None, "Email and password are required"
        
        email = email.lower().strip()
        
        # Find user by email
        user_id = self._email_index.get(email)
        if not user_id:
            return None, "Invalid email or password"
        
        user = self._users.get(user_id)
        if not user:
            return None, "Invalid email or password"
        
        # Verify password
        if not user.password_hash:
            return None, "Invalid email or password"
        
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None, "Invalid email or password"
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        return user, None

    def create_anonymous_session(self) -> Tuple[str, User]:
        """
        Create an anonymous user session.
        
        Returns:
            Tuple of (session_id, User).
        """
        # Create anonymous user
        user = User(
            name="Anonymous User",
            is_anonymous=True
        )
        
        # Store user
        self._users[user.id] = user
        
        # Create session
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = user.id
        
        return session_id, user
    
    def create_session(self, user_id: str) -> str:
        """Create a session for an authenticated user."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = user_id
        return session_id
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user by session ID."""
        user_id = self._sessions.get(session_id)
        if not user_id:
            return None
        return self._users.get(user_id)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        email = email.lower().strip()
        user_id = self._email_index.get(email)
        if not user_id:
            return None
        return self._users.get(user_id)
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session (logout)."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def clear_all(self):
        """Clear all users and sessions (for testing)."""
        self._users.clear()
        self._email_index.clear()
        self._sessions.clear()


# Global auth service instance
auth_service = AuthService()
