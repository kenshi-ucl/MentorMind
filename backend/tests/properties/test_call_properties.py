"""
Property-based tests for call functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, Phase
import uuid
from app import create_app
from app.database import db
from app.models.user import User
from app.models.friend import Friend
from app.models.direct_chat import DirectChat
from app.models.call import Call, CallParticipant
from app.services.call_service import CallService


def get_app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


def create_test_user(name, email):
    """Helper to create a test user."""
    unique_email = f"{uuid.uuid4().hex[:8]}_{email}"
    user = User(
        name=name,
        email=unique_email,
        is_anonymous=False
    )
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


def create_direct_chat(user1_id, user2_id):
    """Helper to create a direct chat."""
    chat = DirectChat(user1_id=user1_id, user2_id=user2_id)
    db.session.add(chat)
    db.session.commit()
    return chat


# Property 6: Call State Consistency
@given(
    call_type=st.sampled_from(['voice', 'video'])
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_call_state_consistency(call_type):
    """Property 6: Call state transitions are valid."""
    app = get_app()
    call_service = CallService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        chat = create_direct_chat(user1.id, user2.id)
        
        call, error = call_service.initiate_call(
            user1.id, call_type, 'direct', chat.id
        )
        assert call is not None
        assert call.status == 'ringing'
        
        participant, _ = call_service.join_call(call.id, user2.id)
        assert participant is not None
        
        call = Call.query.get(call.id)
        assert call.status == 'active'
        
        success, _ = call_service.end_call(call.id, user1.id)
        assert success
        
        call = Call.query.get(call.id)
        assert call.status == 'ended'
        
        db.drop_all()


# Property 10: Call Timeout Behavior
@given(
    call_type=st.sampled_from(['voice', 'video'])
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_call_timeout_behavior(call_type):
    """Property 10: Unanswered calls can be timed out."""
    app = get_app()
    call_service = CallService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        chat = create_direct_chat(user1.id, user2.id)
        
        call, _ = call_service.initiate_call(
            user1.id, call_type, 'direct', chat.id
        )
        assert call.status == 'ringing'
        
        success, error = call_service.timeout_call(call.id)
        assert success
        
        call = Call.query.get(call.id)
        assert call.status == 'missed'
        assert call.ended_at is not None
        
        db.drop_all()


# Property: Cannot join ended call
@given(
    call_type=st.sampled_from(['voice', 'video'])
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_cannot_join_ended_call(call_type):
    """Cannot join a call that has already ended."""
    app = get_app()
    call_service = CallService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        chat = create_direct_chat(user1.id, user2.id)
        
        call, _ = call_service.initiate_call(
            user1.id, call_type, 'direct', chat.id
        )
        call_service.end_call(call.id, user1.id)
        
        participant, error = call_service.join_call(call.id, user2.id)
        
        assert participant is None
        assert error is not None
        assert "no longer available" in error.lower()
        
        db.drop_all()


# Property: Media state updates
@given(
    is_muted=st.booleans(),
    is_video_off=st.booleans()
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_media_state_updates(is_muted, is_video_off):
    """Media state should be correctly updated."""
    app = get_app()
    call_service = CallService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        chat = create_direct_chat(user1.id, user2.id)
        
        call, _ = call_service.initiate_call(
            user1.id, 'video', 'direct', chat.id
        )
        
        participant, error = call_service.update_media_state(
            call.id, user1.id,
            is_muted=is_muted,
            is_video_off=is_video_off
        )
        
        assert participant is not None
        assert participant.is_muted == is_muted
        assert participant.is_video_off == is_video_off
        
        db.drop_all()


# Property: No duplicate active calls
@given(
    call_type=st.sampled_from(['voice', 'video'])
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_no_duplicate_active_calls(call_type):
    """Cannot initiate a new call when one is already active."""
    app = get_app()
    call_service = CallService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        chat = create_direct_chat(user1.id, user2.id)
        
        call1, _ = call_service.initiate_call(
            user1.id, call_type, 'direct', chat.id
        )
        assert call1 is not None
        
        call2, error = call_service.initiate_call(
            user1.id, call_type, 'direct', chat.id
        )
        
        assert call2 is None
        assert error is not None
        assert "already" in error.lower()
        
        db.drop_all()
