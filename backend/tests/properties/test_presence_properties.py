"""
Property-based tests for presence functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, Phase
import uuid
from app import create_app
from app.database import db
from app.models.user import User
from app.models.friend import Friend
from app.services.presence_service import PresenceService


def get_app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


def create_test_user(name, email):
    """Helper to create a test user."""
    unique_email = f"{uuid.uuid4().hex[:8]}_{email}"
    user = User(name=name, email=unique_email, is_anonymous=False)
    db.session.add(user)
    db.session.commit()
    return user


def create_friendship(user1_id, user2_id):
    """Helper to create a bidirectional friendship."""
    friend1 = Friend(user_id=user1_id, friend_id=user2_id)
    friend2 = Friend(user_id=user2_id, friend_id=user1_id)
    db.session.add(friend1)
    db.session.add(friend2)
    db.session.commit()


# Property 8: Presence Consistency
@given(socket_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_presence_consistency(socket_id):
    """Property 8: Presence state is consistent."""
    app = get_app()
    presence_service = PresenceService()
    
    with app.app_context():
        db.create_all()
        
        user = create_test_user("User", "user@test.com")
        
        presence = presence_service.set_online(user.id, socket_id.strip())
        assert presence.is_online
        assert presence.socket_id == socket_id.strip()
        
        presence_data = presence_service.get_presence(user.id)
        assert presence_data['isOnline']
        
        presence = presence_service.set_offline(user.id)
        assert not presence.is_online
        assert presence.socket_id is None
        
        presence_data = presence_service.get_presence(user.id)
        assert not presence_data['isOnline']
        
        db.drop_all()


# Property: Friends presence visibility
@given(friend_count=st.integers(min_value=1, max_value=5))
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_friends_presence_visibility(friend_count):
    """Friends presence should be visible to each other."""
    app = get_app()
    presence_service = PresenceService()
    
    with app.app_context():
        db.create_all()
        
        main_user = create_test_user("MainUser", "main@test.com")
        
        friends = []
        for i in range(friend_count):
            friend = create_test_user(f"Friend{i}", f"friend{i}@test.com")
            create_friendship(main_user.id, friend.id)
            friends.append(friend)
        
        online_count = friend_count // 2 + 1
        for i in range(online_count):
            presence_service.set_online(friends[i].id, f"socket_{i}")
        
        presences = presence_service.get_friends_presence(main_user.id)
        
        assert len(presences) == friend_count
        online_presences = [p for p in presences if p['isOnline']]
        assert len(online_presences) == online_count
        
        db.drop_all()


# Property: Status updates
@given(status=st.sampled_from(['available', 'busy', 'away', 'in_call']))
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_status_updates(status):
    """Status should be correctly updated."""
    app = get_app()
    presence_service = PresenceService()
    
    with app.app_context():
        db.create_all()
        
        user = create_test_user("User", "user@test.com")
        presence_service.set_online(user.id, "socket_123")
        
        presence = presence_service.set_status(user.id, status)
        
        assert presence.current_status == status
        
        presence_data = presence_service.get_presence(user.id)
        assert presence_data['status'] == status
        
        db.drop_all()
