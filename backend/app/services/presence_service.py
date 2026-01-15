"""
Presence service for tracking user online status.
"""
from datetime import datetime
from typing import List, Optional, Dict
from app.database import db
from app.models.user_presence import UserPresence
from app.models.friend import Friend


class PresenceService:
    """Service for managing user presence/online status."""
    
    def set_online(self, user_id: str, socket_id: str = None) -> UserPresence:
        """
        Set a user as online.
        
        Args:
            user_id: The user's ID
            socket_id: Optional WebSocket connection ID
            
        Returns:
            UserPresence object
        """
        presence = UserPresence.query.filter_by(user_id=user_id).first()
        
        if presence:
            presence.is_online = True
            presence.socket_id = socket_id
            presence.last_seen = datetime.utcnow()
            presence.current_status = 'available'
        else:
            presence = UserPresence(
                user_id=user_id,
                is_online=True,
                socket_id=socket_id,
                last_seen=datetime.utcnow(),
                current_status='available'
            )
            db.session.add(presence)
        
        db.session.commit()
        return presence
    
    def set_offline(self, user_id: str) -> Optional[UserPresence]:
        """
        Set a user as offline.
        
        Args:
            user_id: The user's ID
            
        Returns:
            UserPresence object or None
        """
        presence = UserPresence.query.filter_by(user_id=user_id).first()
        
        if presence:
            presence.is_online = False
            presence.socket_id = None
            presence.last_seen = datetime.utcnow()
            presence.current_status = 'available'
            db.session.commit()
        
        return presence
    
    def set_status(self, user_id: str, status: str) -> Optional[UserPresence]:
        """
        Set a user's status.
        
        Args:
            user_id: The user's ID
            status: Status string ('available', 'busy', 'away', 'in_call')
            
        Returns:
            UserPresence object or None
        """
        valid_statuses = ['available', 'busy', 'away', 'in_call']
        if status not in valid_statuses:
            return None
        
        presence = UserPresence.query.filter_by(user_id=user_id).first()
        
        if presence:
            presence.current_status = status
            db.session.commit()
        
        return presence
    
    def get_presence(self, user_id: str) -> Optional[dict]:
        """
        Get a user's presence status.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Presence dictionary or None
        """
        presence = UserPresence.query.filter_by(user_id=user_id).first()
        
        if presence:
            return presence.to_dict()
        
        # Return default offline status if no presence record
        return {
            'userId': user_id,
            'isOnline': False,
            'lastSeen': None,
            'status': 'available'
        }
    
    def get_friends_presence(self, user_id: str) -> List[dict]:
        """
        Get online status of all friends.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of presence dictionaries for friends
        """
        # Get all friend IDs
        friendships = Friend.query.filter_by(user_id=user_id).all()
        friend_ids = [f.friend_id for f in friendships]
        
        if not friend_ids:
            return []
        
        # Get presence for all friends
        presences = UserPresence.query.filter(
            UserPresence.user_id.in_(friend_ids)
        ).all()
        
        # Create a map of user_id to presence
        presence_map = {p.user_id: p.to_dict() for p in presences}
        
        # Return presence for all friends (default to offline if no record)
        result = []
        for friend_id in friend_ids:
            if friend_id in presence_map:
                result.append(presence_map[friend_id])
            else:
                result.append({
                    'userId': friend_id,
                    'isOnline': False,
                    'lastSeen': None,
                    'status': 'available'
                })
        
        return result
    
    def get_online_friends(self, user_id: str) -> List[str]:
        """
        Get list of online friend IDs.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of online friend user IDs
        """
        # Get all friend IDs
        friendships = Friend.query.filter_by(user_id=user_id).all()
        friend_ids = [f.friend_id for f in friendships]
        
        if not friend_ids:
            return []
        
        # Get online friends
        online_presences = UserPresence.query.filter(
            UserPresence.user_id.in_(friend_ids),
            UserPresence.is_online == True
        ).all()
        
        return [p.user_id for p in online_presences]
    
    def get_socket_id(self, user_id: str) -> Optional[str]:
        """
        Get a user's current socket ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Socket ID or None
        """
        presence = UserPresence.query.filter_by(user_id=user_id).first()
        
        if presence and presence.is_online:
            return presence.socket_id
        
        return None
    
    def get_socket_ids_for_users(self, user_ids: List[str]) -> Dict[str, str]:
        """
        Get socket IDs for multiple users.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            Dictionary mapping user_id to socket_id
        """
        presences = UserPresence.query.filter(
            UserPresence.user_id.in_(user_ids),
            UserPresence.is_online == True
        ).all()
        
        return {p.user_id: p.socket_id for p in presences if p.socket_id}


# Singleton instance
presence_service = PresenceService()
