"""
Friend service for managing friendships and friend requests.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import or_, and_
from app.database import db
from app.models.friend import Friend
from app.models.friend_request import FriendRequest
from app.models.user import User


class FriendService:
    """Service for managing friendships and friend requests."""
    
    def get_friends(self, user_id: str) -> List[dict]:
        """
        Get all friends for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of friend user dictionaries
        """
        friendships = Friend.query.filter_by(user_id=user_id).all()
        friends = []
        
        for friendship in friendships:
            friend_user = User.query.get(friendship.friend_id)
            if friend_user:
                friend_data = friend_user.to_dict()
                friend_data['friendshipId'] = friendship.id
                friend_data['friendsSince'] = friendship.created_at.isoformat() if friendship.created_at else None
                friends.append(friend_data)
        
        return friends
    
    def search_users(self, query: str, current_user_id: str, limit: int = 20) -> List[dict]:
        """
        Search for users by name or email.
        
        Args:
            query: Search query string
            current_user_id: Current user's ID to exclude from results
            limit: Maximum number of results
            
        Returns:
            List of matching user dictionaries
        """
        if not query or len(query) < 2:
            return []
        
        search_pattern = f"%{query}%"
        
        users = User.query.filter(
            and_(
                User.id != current_user_id,
                User.is_anonymous == False,
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        ).limit(limit).all()
        
        # Get existing friendships and pending requests
        existing_friend_ids = set(
            f.friend_id for f in Friend.query.filter_by(user_id=current_user_id).all()
        )
        
        pending_request_ids = set(
            r.recipient_id for r in FriendRequest.query.filter_by(
                sender_id=current_user_id, status='pending'
            ).all()
        )
        
        received_request_ids = set(
            r.sender_id for r in FriendRequest.query.filter_by(
                recipient_id=current_user_id, status='pending'
            ).all()
        )
        
        results = []
        for user in users:
            user_data = user.to_dict()
            user_data['isFriend'] = user.id in existing_friend_ids
            user_data['hasPendingRequest'] = user.id in pending_request_ids
            user_data['hasReceivedRequest'] = user.id in received_request_ids
            results.append(user_data)
        
        return results
    
    def send_friend_request(self, sender_id: str, recipient_id: str) -> Tuple[Optional[FriendRequest], Optional[str]]:
        """
        Send a friend request.
        
        Args:
            sender_id: ID of the user sending the request
            recipient_id: ID of the user receiving the request
            
        Returns:
            Tuple of (FriendRequest, error_message)
        """
        # Validate: cannot send request to self
        if sender_id == recipient_id:
            return None, "Cannot send friend request to yourself"
        
        # Check if recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            return None, "User not found"
        
        # Check if already friends
        existing_friendship = Friend.query.filter_by(
            user_id=sender_id, friend_id=recipient_id
        ).first()
        if existing_friendship:
            return None, "Already friends with this user"
        
        # Check for existing pending request (either direction)
        existing_request = FriendRequest.query.filter(
            or_(
                and_(FriendRequest.sender_id == sender_id, 
                     FriendRequest.recipient_id == recipient_id,
                     FriendRequest.status == 'pending'),
                and_(FriendRequest.sender_id == recipient_id,
                     FriendRequest.recipient_id == sender_id,
                     FriendRequest.status == 'pending')
            )
        ).first()
        
        if existing_request:
            if existing_request.sender_id == sender_id:
                return None, "Friend request already sent"
            else:
                return None, "This user has already sent you a friend request"
        
        # Create new friend request
        friend_request = FriendRequest(
            sender_id=sender_id,
            recipient_id=recipient_id,
            status='pending'
        )
        
        db.session.add(friend_request)
        db.session.commit()
        
        return friend_request, None
    
    def get_pending_requests(self, user_id: str) -> List[dict]:
        """
        Get all pending friend requests for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of pending friend request dictionaries
        """
        requests = FriendRequest.query.filter_by(
            recipient_id=user_id,
            status='pending'
        ).order_by(FriendRequest.created_at.desc()).all()
        
        return [req.to_dict(include_users=True) for req in requests]
    
    def get_sent_requests(self, user_id: str) -> List[dict]:
        """
        Get all sent friend requests for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of sent friend request dictionaries
        """
        requests = FriendRequest.query.filter_by(
            sender_id=user_id,
            status='pending'
        ).order_by(FriendRequest.created_at.desc()).all()
        
        return [req.to_dict(include_users=True) for req in requests]
    
    def accept_request(self, request_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Accept a friend request, creating bidirectional friendship.
        
        Args:
            request_id: ID of the friend request
            user_id: ID of the user accepting (must be recipient)
            
        Returns:
            Tuple of (success, error_message)
        """
        friend_request = FriendRequest.query.get(request_id)
        
        if not friend_request:
            return False, "Friend request not found"
        
        if friend_request.recipient_id != user_id:
            return False, "Not authorized to accept this request"
        
        if friend_request.status != 'pending':
            return False, "Friend request is no longer pending"
        
        # Create bidirectional friendship
        friendship1 = Friend(
            user_id=friend_request.recipient_id,
            friend_id=friend_request.sender_id
        )
        friendship2 = Friend(
            user_id=friend_request.sender_id,
            friend_id=friend_request.recipient_id
        )
        
        # Update request status
        friend_request.status = 'accepted'
        friend_request.updated_at = datetime.utcnow()
        
        db.session.add(friendship1)
        db.session.add(friendship2)
        db.session.commit()
        
        return True, None
    
    def decline_request(self, request_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Decline a friend request.
        
        Args:
            request_id: ID of the friend request
            user_id: ID of the user declining (must be recipient)
            
        Returns:
            Tuple of (success, error_message)
        """
        friend_request = FriendRequest.query.get(request_id)
        
        if not friend_request:
            return False, "Friend request not found"
        
        if friend_request.recipient_id != user_id:
            return False, "Not authorized to decline this request"
        
        if friend_request.status != 'pending':
            return False, "Friend request is no longer pending"
        
        friend_request.status = 'declined'
        friend_request.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, None
    
    def remove_friend(self, user_id: str, friend_id: str) -> Tuple[bool, Optional[str]]:
        """
        Remove a friendship (bidirectional).
        
        Args:
            user_id: Current user's ID
            friend_id: Friend's user ID
            
        Returns:
            Tuple of (success, error_message)
        """
        # Find and delete both directions of the friendship
        friendship1 = Friend.query.filter_by(
            user_id=user_id, friend_id=friend_id
        ).first()
        
        friendship2 = Friend.query.filter_by(
            user_id=friend_id, friend_id=user_id
        ).first()
        
        if not friendship1 and not friendship2:
            return False, "Friendship not found"
        
        if friendship1:
            db.session.delete(friendship1)
        if friendship2:
            db.session.delete(friendship2)
        
        db.session.commit()
        
        return True, None
    
    def are_friends(self, user_id: str, other_user_id: str) -> bool:
        """Check if two users are friends."""
        friendship = Friend.query.filter_by(
            user_id=user_id, friend_id=other_user_id
        ).first()
        return friendship is not None


# Singleton instance
friend_service = FriendService()
