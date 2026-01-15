"""
Property-based tests for friend management functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck, Phase
from app import create_app
from app.database import db
from app.models.user import User
from app.models.friend import Friend
from app.models.friend_request import FriendRequest
from app.services.friend_service import FriendService
import uuid


def get_app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


def create_test_user(name, email):
    """Helper to create a test user."""
    # Add UUID to ensure uniqueness
    unique_email = f"{uuid.uuid4().hex[:8]}_{email}"
    user = User(
        name=name,
        email=unique_email,
        is_anonymous=False
    )
    db.session.add(user)
    db.session.commit()
    return user


# Property 1: Friend Request Symmetry
@given(
    name1=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    name2=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_friend_request_symmetry(name1, name2):
    """Property 1: Accepted friend request creates bidirectional friendship."""
    assume(name1.strip() != name2.strip())
    
    app = get_app()
    friend_service = FriendService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user(name1.strip(), "user1@test.com")
        user2 = create_test_user(name2.strip(), "user2@test.com")
        
        request, error = friend_service.send_friend_request(user1.id, user2.id)
        assert error is None
        assert request is not None
        
        success, error = friend_service.accept_request(request.id, user2.id)
        assert success
        assert error is None
        
        assert friend_service.are_friends(user1.id, user2.id)
        assert friend_service.are_friends(user2.id, user1.id)
        
        db.drop_all()


# Property 2: No Self-Friendship
@given(name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_no_self_friendship(name):
    """Property 2: Cannot send friend request to yourself."""
    app = get_app()
    friend_service = FriendService()
    
    with app.app_context():
        db.create_all()
        
        user = create_test_user(name.strip(), "user@test.com")
        
        request, error = friend_service.send_friend_request(user.id, user.id)
        
        assert request is None
        assert error is not None
        assert "yourself" in error.lower()
        
        db.drop_all()


# Property 3: No Duplicate Friend Requests
@given(
    name1=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    name2=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_no_duplicate_friend_requests(name1, name2):
    """Property 3: Cannot send duplicate friend requests."""
    assume(name1.strip() != name2.strip())
    
    app = get_app()
    friend_service = FriendService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user(name1.strip(), "user1@test.com")
        user2 = create_test_user(name2.strip(), "user2@test.com")
        
        request1, error1 = friend_service.send_friend_request(user1.id, user2.id)
        assert error1 is None
        assert request1 is not None
        
        request2, error2 = friend_service.send_friend_request(user1.id, user2.id)
        
        assert request2 is None
        assert error2 is not None
        assert "already" in error2.lower()
        
        db.drop_all()


# Property 5: Bidirectional Friend Removal
@given(
    name1=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    name2=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_bidirectional_friend_removal(name1, name2):
    """Property 5: Removing a friend removes the relationship from both sides."""
    assume(name1.strip() != name2.strip())
    
    app = get_app()
    friend_service = FriendService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user(name1.strip(), "user1@test.com")
        user2 = create_test_user(name2.strip(), "user2@test.com")
        
        request, _ = friend_service.send_friend_request(user1.id, user2.id)
        friend_service.accept_request(request.id, user2.id)
        
        assert friend_service.are_friends(user1.id, user2.id)
        assert friend_service.are_friends(user2.id, user1.id)
        
        success, error = friend_service.remove_friend(user1.id, user2.id)
        assert success
        assert error is None
        
        assert not friend_service.are_friends(user1.id, user2.id)
        assert not friend_service.are_friends(user2.id, user1.id)
        
        db.drop_all()
