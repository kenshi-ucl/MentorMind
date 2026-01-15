"""
Property-based tests for messaging functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, Phase
import uuid
from app import create_app
from app.database import db
from app.models.user import User
from app.models.friend import Friend
from app.models.direct_chat import DirectChat
from app.models.message import DirectMessage
from app.services.chat_service import ChatService


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


# Property 4: Message Ordering Preservation
@given(
    messages=st.lists(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_message_ordering_preservation(messages):
    """Property 4: Messages are returned in chronological order."""
    app = get_app()
    chat_service = ChatService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        
        chat, _ = chat_service.get_or_create_direct_chat(user1.id, user2.id)
        assert chat is not None
        
        sent_messages = []
        for i, content in enumerate(messages):
            sender = user1 if i % 2 == 0 else user2
            msg, _ = chat_service.send_message(chat.id, sender.id, content.strip())
            if msg:
                sent_messages.append(msg)
        
        retrieved, _ = chat_service.get_messages(chat.id, user1.id, limit=100)
        
        assert len(retrieved) == len(sent_messages)
        
        for i in range(len(retrieved) - 1):
            assert retrieved[i]['createdAt'] <= retrieved[i + 1]['createdAt']
        
        db.drop_all()


# Property: Message content integrity
@given(
    content=st.text(min_size=1, max_size=500).filter(lambda x: x.strip())
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_message_content_integrity(content):
    """Messages should preserve their content exactly."""
    app = get_app()
    chat_service = ChatService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        
        chat, _ = chat_service.get_or_create_direct_chat(user1.id, user2.id)
        
        msg, _ = chat_service.send_message(chat.id, user1.id, content.strip())
        assert msg is not None
        
        messages, _ = chat_service.get_messages(chat.id, user1.id)
        assert len(messages) == 1
        assert messages[0]['content'] == content.strip()
        
        db.drop_all()


# Property: Only friends can chat
@given(
    content=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_only_friends_can_chat(content):
    """Non-friends should not be able to create a chat."""
    app = get_app()
    chat_service = ChatService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        
        chat, error = chat_service.get_or_create_direct_chat(user1.id, user2.id)
        
        assert chat is None
        assert error is not None
        assert "friends" in error.lower()
        
        db.drop_all()


# Property: Read status tracking
@given(
    message_count=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_read_status_tracking(message_count):
    """Read status should be tracked correctly."""
    app = get_app()
    chat_service = ChatService()
    
    with app.app_context():
        db.create_all()
        
        user1 = create_test_user("User1", "user1@test.com")
        user2 = create_test_user("User2", "user2@test.com")
        create_friendship(user1.id, user2.id)
        
        chat, _ = chat_service.get_or_create_direct_chat(user1.id, user2.id)
        
        for i in range(message_count):
            chat_service.send_message(chat.id, user1.id, f"Message {i}")
        
        count, _ = chat_service.mark_as_read(chat.id, user2.id)
        
        assert count == message_count
        
        messages, _ = chat_service.get_messages(chat.id, user2.id)
        for msg in messages:
            assert user2.id in msg['readBy']
        
        db.drop_all()
