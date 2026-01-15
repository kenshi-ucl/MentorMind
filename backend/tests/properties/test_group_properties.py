"""
Property-based tests for group learning functionality.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, Phase
import uuid
from app import create_app
from app.database import db
from app.models.user import User
from app.models.friend import Friend
from app.models.group_learning import GroupLearning
from app.models.group_member import GroupMember
from app.services.group_service import GroupService


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


# Property 7: Group Membership Integrity
@given(
    group_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    member_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_group_membership_integrity(group_name, member_count):
    """Property 7: Group membership is consistent."""
    app = get_app()
    group_service = GroupService()
    
    with app.app_context():
        db.create_all()
        
        creator = create_test_user("Creator", "creator@test.com")
        
        group, error = group_service.create_group(creator.id, group_name.strip())
        assert group is not None
        assert error is None
        
        groups = group_service.get_user_groups(creator.id)
        assert len(groups) == 1
        assert groups[0]['userRole'] == 'creator'
        
        members = []
        for i in range(member_count):
            member = create_test_user(f"Member{i}", f"member{i}@test.com")
            create_friendship(creator.id, member.id)
            members.append(member)
        
        successful, failed = group_service.invite_to_group(
            group.id, creator.id, [m.id for m in members]
        )
        assert len(successful) == member_count
        
        for member in members:
            success, _ = group_service.join_group(group.id, member.id)
            assert success
        
        group_data, _ = group_service.get_group(group.id, creator.id)
        assert group_data['memberCount'] == member_count + 1
        
        db.drop_all()


# Property: Creator cannot leave group
@given(group_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_creator_cannot_leave(group_name):
    """Group creator cannot leave their own group."""
    app = get_app()
    group_service = GroupService()
    
    with app.app_context():
        db.create_all()
        
        creator = create_test_user("Creator", "creator@test.com")
        group, _ = group_service.create_group(creator.id, group_name.strip())
        
        success, error = group_service.leave_group(group.id, creator.id)
        
        assert not success
        assert error is not None
        assert "creator" in error.lower()
        
        db.drop_all()


# Property: Only creator can remove members
@given(group_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()))
@settings(max_examples=10, deadline=None, phases=[Phase.generate])
def test_only_creator_can_remove(group_name):
    """Only the creator can remove members."""
    app = get_app()
    group_service = GroupService()
    
    with app.app_context():
        db.create_all()
        
        creator = create_test_user("Creator", "creator@test.com")
        member1 = create_test_user("Member1", "member1@test.com")
        member2 = create_test_user("Member2", "member2@test.com")
        
        create_friendship(creator.id, member1.id)
        create_friendship(creator.id, member2.id)
        
        group, _ = group_service.create_group(creator.id, group_name.strip())
        group_service.invite_to_group(group.id, creator.id, [member1.id, member2.id])
        group_service.join_group(group.id, member1.id)
        group_service.join_group(group.id, member2.id)
        
        success, error = group_service.remove_member(group.id, member1.id, member2.id)
        assert not success
        assert "creator" in error.lower()
        
        success, error = group_service.remove_member(group.id, creator.id, member2.id)
        assert success
        
        db.drop_all()
