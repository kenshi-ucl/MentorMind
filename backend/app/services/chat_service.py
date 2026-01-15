"""
Chat service for managing direct messages between friends.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import or_, and_
from app.database import db
from app.models.direct_chat import DirectChat
from app.models.message import DirectMessage
from app.models.friend import Friend


class ChatService:
    """Service for managing direct chats and messages."""
    
    def get_or_create_direct_chat(self, user1_id: str, user2_id: str) -> Tuple[Optional[DirectChat], Optional[str]]:
        """
        Get existing direct chat or create a new one.
        
        Args:
            user1_id: First user's ID
            user2_id: Second user's ID
            
        Returns:
            Tuple of (DirectChat, error_message)
        """
        if user1_id == user2_id:
            return None, "Cannot create chat with yourself"
        
        # Check if users are friends
        friendship = Friend.query.filter_by(
            user_id=user1_id, friend_id=user2_id
        ).first()
        
        if not friendship:
            return None, "Users must be friends to chat"
        
        # Look for existing chat (either direction)
        chat = DirectChat.query.filter(
            or_(
                and_(DirectChat.user1_id == user1_id, DirectChat.user2_id == user2_id),
                and_(DirectChat.user1_id == user2_id, DirectChat.user2_id == user1_id)
            )
        ).first()
        
        if chat:
            return chat, None
        
        # Create new chat
        chat = DirectChat(
            user1_id=user1_id,
            user2_id=user2_id
        )
        
        db.session.add(chat)
        db.session.commit()
        
        return chat, None
    
    def get_user_chats(self, user_id: str) -> List[dict]:
        """
        Get all direct chats for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of chat dictionaries with last message info
        """
        chats = DirectChat.query.filter(
            or_(
                DirectChat.user1_id == user_id,
                DirectChat.user2_id == user_id
            )
        ).order_by(DirectChat.last_message_at.desc()).all()
        
        result = []
        for chat in chats:
            chat_data = chat.to_dict(current_user_id=user_id)
            
            # Get last message
            last_message = DirectMessage.query.filter_by(
                chat_id=chat.id
            ).order_by(DirectMessage.created_at.desc()).first()
            
            if last_message:
                chat_data['lastMessage'] = last_message.to_dict()
            
            # Count unread messages
            unread_count = DirectMessage.query.filter(
                and_(
                    DirectMessage.chat_id == chat.id,
                    DirectMessage.sender_id != user_id,
                    ~DirectMessage.read_by.contains([user_id])
                )
            ).count()
            chat_data['unreadCount'] = unread_count
            
            result.append(chat_data)
        
        return result
    
    def get_messages(self, chat_id: str, user_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[dict], Optional[str]]:
        """
        Get messages for a chat with pagination.
        
        Args:
            chat_id: The chat's ID
            user_id: Current user's ID (for authorization)
            limit: Maximum number of messages
            offset: Number of messages to skip
            
        Returns:
            Tuple of (messages list, error_message)
        """
        chat = DirectChat.query.get(chat_id)
        
        if not chat:
            return [], "Chat not found"
        
        # Verify user is part of the chat
        if chat.user1_id != user_id and chat.user2_id != user_id:
            return [], "Not authorized to view this chat"
        
        messages = DirectMessage.query.filter_by(
            chat_id=chat_id
        ).order_by(DirectMessage.created_at.desc()).offset(offset).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        return [msg.to_dict() for msg in messages], None
    
    def send_message(self, chat_id: str, sender_id: str, content: str) -> Tuple[Optional[DirectMessage], Optional[str]]:
        """
        Send a message in a direct chat.
        
        Args:
            chat_id: The chat's ID
            sender_id: Sender's user ID
            content: Message content
            
        Returns:
            Tuple of (DirectMessage, error_message)
        """
        if not content or not content.strip():
            return None, "Message content cannot be empty"
        
        chat = DirectChat.query.get(chat_id)
        
        if not chat:
            return None, "Chat not found"
        
        # Verify sender is part of the chat
        if chat.user1_id != sender_id and chat.user2_id != sender_id:
            return None, "Not authorized to send messages in this chat"
        
        # Create message
        message = DirectMessage(
            chat_id=chat_id,
            sender_id=sender_id,
            content=content.strip(),
            read_by=[sender_id]  # Sender has read their own message
        )
        
        # Update chat's last_message_at
        chat.last_message_at = datetime.utcnow()
        
        db.session.add(message)
        db.session.commit()
        
        return message, None
    
    def mark_as_read(self, chat_id: str, user_id: str, message_ids: Optional[List[str]] = None) -> Tuple[int, Optional[str]]:
        """
        Mark messages as read by a user.
        
        Args:
            chat_id: The chat's ID
            user_id: User marking messages as read
            message_ids: Optional list of specific message IDs (marks all if None)
            
        Returns:
            Tuple of (count of updated messages, error_message)
        """
        chat = DirectChat.query.get(chat_id)
        
        if not chat:
            return 0, "Chat not found"
        
        # Verify user is part of the chat
        if chat.user1_id != user_id and chat.user2_id != user_id:
            return 0, "Not authorized to access this chat"
        
        # Get messages to mark as read
        query = DirectMessage.query.filter(
            and_(
                DirectMessage.chat_id == chat_id,
                DirectMessage.sender_id != user_id
            )
        )
        
        if message_ids:
            query = query.filter(DirectMessage.id.in_(message_ids))
        
        messages = query.all()
        updated_count = 0
        
        for message in messages:
            read_by = list(message.read_by or [])
            if user_id not in read_by:
                read_by.append(user_id)
                message.read_by = read_by
                # Flag the JSON column as modified for SQLAlchemy
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(message, 'read_by')
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
        
        return updated_count, None


# Singleton instance
chat_service = ChatService()
