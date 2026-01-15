"""
Group service for managing group learning sessions.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from app.database import db
from app.models.group_learning import GroupLearning
from app.models.group_member import GroupMember
from app.models.message import GroupMessage
from app.models.friend import Friend


class GroupService:
    """Service for managing group learning sessions."""
    
    def create_group(self, creator_id: str, name: str, description: str = None) -> Tuple[Optional[GroupLearning], Optional[str]]:
        """
        Create a new group learning session.
        
        Args:
            creator_id: ID of the user creating the group
            name: Name of the group
            description: Optional description
            
        Returns:
            Tuple of (GroupLearning, error_message)
        """
        if not name or not name.strip():
            return None, "Group name is required"
        
        # Create group
        group = GroupLearning(
            name=name.strip(),
            description=description.strip() if description else None,
            creator_id=creator_id
        )
        
        db.session.add(group)
        db.session.flush()  # Get the group ID
        
        # Add creator as a member with 'creator' role
        creator_member = GroupMember(
            group_id=group.id,
            user_id=creator_id,
            role='creator',
            status='active',
            joined_at=datetime.utcnow()
        )
        
        db.session.add(creator_member)
        db.session.commit()
        
        return group, None
    
    def get_user_groups(self, user_id: str) -> List[dict]:
        """
        Get all groups a user is a member of.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of group dictionaries
        """
        memberships = GroupMember.query.filter_by(
            user_id=user_id,
            status='active'
        ).all()
        
        groups = []
        for membership in memberships:
            group = GroupLearning.query.get(membership.group_id)
            if group:
                group_data = group.to_dict()
                group_data['userRole'] = membership.role
                group_data['joinedAt'] = membership.joined_at.isoformat() if membership.joined_at else None
                groups.append(group_data)
        
        return sorted(groups, key=lambda g: g.get('lastActivityAt', ''), reverse=True)
    
    def get_group(self, group_id: str, user_id: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Get group details.
        
        Args:
            group_id: The group's ID
            user_id: Current user's ID (for authorization)
            
        Returns:
            Tuple of (group dict, error_message)
        """
        group = GroupLearning.query.get(group_id)
        
        if not group:
            return None, "Group not found"
        
        # Check if user is a member
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not membership:
            return None, "Not a member of this group"
        
        group_data = group.to_dict(include_members=True)
        group_data['userRole'] = membership.role
        
        return group_data, None
    
    def invite_to_group(self, group_id: str, inviter_id: str, invitee_ids: List[str]) -> Tuple[List[str], List[str]]:
        """
        Invite friends to a group.
        
        Args:
            group_id: The group's ID
            inviter_id: ID of the user sending invites
            invitee_ids: List of user IDs to invite
            
        Returns:
            Tuple of (successful_invites, failed_invites)
        """
        group = GroupLearning.query.get(group_id)
        
        if not group:
            return [], invitee_ids
        
        # Check if inviter is a member
        inviter_membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=inviter_id,
            status='active'
        ).first()
        
        if not inviter_membership:
            return [], invitee_ids
        
        successful = []
        failed = []
        
        for invitee_id in invitee_ids:
            # Check if they're friends
            friendship = Friend.query.filter_by(
                user_id=inviter_id,
                friend_id=invitee_id
            ).first()
            
            if not friendship:
                failed.append(invitee_id)
                continue
            
            # Check if already a member or has pending invite
            existing = GroupMember.query.filter_by(
                group_id=group_id,
                user_id=invitee_id
            ).first()
            
            if existing:
                if existing.status in ['active', 'pending']:
                    failed.append(invitee_id)
                    continue
                # Reactivate if they left
                existing.status = 'pending'
                existing.joined_at = None
            else:
                # Create new pending membership
                member = GroupMember(
                    group_id=group_id,
                    user_id=invitee_id,
                    role='member',
                    status='pending'
                )
                db.session.add(member)
            
            successful.append(invitee_id)
        
        if successful:
            db.session.commit()
        
        return successful, failed
    
    def join_group(self, group_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Accept a group invitation and join.
        
        Args:
            group_id: The group's ID
            user_id: ID of the user joining
            
        Returns:
            Tuple of (success, error_message)
        """
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id
        ).first()
        
        if not membership:
            return False, "No invitation found for this group"
        
        if membership.status == 'active':
            return False, "Already a member of this group"
        
        if membership.status != 'pending':
            return False, "Invitation is no longer valid"
        
        membership.status = 'active'
        membership.joined_at = datetime.utcnow()
        
        # Update group activity
        group = GroupLearning.query.get(group_id)
        if group:
            group.last_activity_at = datetime.utcnow()
        
        db.session.commit()
        
        return True, None
    
    def leave_group(self, group_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Leave a group.
        
        Args:
            group_id: The group's ID
            user_id: ID of the user leaving
            
        Returns:
            Tuple of (success, error_message)
        """
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not membership:
            return False, "Not a member of this group"
        
        # Creator cannot leave, they must delete the group
        if membership.role == 'creator':
            return False, "Group creator cannot leave. Delete the group instead."
        
        membership.status = 'left'
        db.session.commit()
        
        return True, None
    
    def decline_invitation(self, group_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Decline a group invitation.
        
        Args:
            group_id: The group's ID
            user_id: ID of the user declining
            
        Returns:
            Tuple of (success, error_message)
        """
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            status='pending'
        ).first()
        
        if not membership:
            return False, "No pending invitation found for this group"
        
        membership.status = 'declined'
        db.session.commit()
        
        return True, None
    
    def remove_member(self, group_id: str, remover_id: str, member_id: str) -> Tuple[bool, Optional[str]]:
        """
        Remove a member from the group (creator only).
        
        Args:
            group_id: The group's ID
            remover_id: ID of the user removing (must be creator)
            member_id: ID of the member to remove
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check if remover is the creator
        remover_membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=remover_id,
            status='active'
        ).first()
        
        if not remover_membership or remover_membership.role != 'creator':
            return False, "Only the group creator can remove members"
        
        # Cannot remove yourself
        if remover_id == member_id:
            return False, "Cannot remove yourself from the group"
        
        # Find the member to remove
        member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=member_id,
            status='active'
        ).first()
        
        if not member:
            return False, "Member not found in this group"
        
        member.status = 'removed'
        db.session.commit()
        
        return True, None
    
    def get_pending_invitations(self, user_id: str) -> List[dict]:
        """
        Get all pending group invitations for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of pending invitation dictionaries
        """
        memberships = GroupMember.query.filter_by(
            user_id=user_id,
            status='pending'
        ).all()
        
        invitations = []
        for membership in memberships:
            group = GroupLearning.query.get(membership.group_id)
            if group:
                invitations.append({
                    'membershipId': membership.id,
                    'group': group.to_dict(),
                    'createdAt': membership.created_at.isoformat() if membership.created_at else None
                })
        
        return invitations
    
    def send_group_message(self, group_id: str, sender_id: str, content: str) -> Tuple[Optional[GroupMessage], Optional[str]]:
        """
        Send a message in a group.
        
        Args:
            group_id: The group's ID
            sender_id: Sender's user ID
            content: Message content
            
        Returns:
            Tuple of (GroupMessage, error_message)
        """
        if not content or not content.strip():
            return None, "Message content cannot be empty"
        
        # Check if sender is a member
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=sender_id,
            status='active'
        ).first()
        
        if not membership:
            return None, "Not a member of this group"
        
        # Create message
        message = GroupMessage(
            group_id=group_id,
            sender_id=sender_id,
            content=content.strip(),
            read_by=[sender_id]
        )
        
        # Update group activity
        group = GroupLearning.query.get(group_id)
        if group:
            group.last_activity_at = datetime.utcnow()
        
        db.session.add(message)
        db.session.commit()
        
        return message, None
    
    def get_group_messages(self, group_id: str, user_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[dict], Optional[str]]:
        """
        Get messages for a group with pagination.
        
        Args:
            group_id: The group's ID
            user_id: Current user's ID (for authorization)
            limit: Maximum number of messages
            offset: Number of messages to skip
            
        Returns:
            Tuple of (messages list, error_message)
        """
        # Check if user is a member
        membership = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not membership:
            return [], "Not a member of this group"
        
        messages = GroupMessage.query.filter_by(
            group_id=group_id
        ).order_by(GroupMessage.created_at.desc()).offset(offset).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        return [msg.to_dict() for msg in messages], None


# Singleton instance
group_service = GroupService()
