"""
Call service for managing voice and video calls.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from app.database import db
from app.models.call import Call, CallParticipant
from app.models.direct_chat import DirectChat
from app.models.group_learning import GroupLearning
from app.models.group_member import GroupMember


class CallService:
    """Service for managing voice and video calls."""
    
    def initiate_call(
        self, 
        initiator_id: str, 
        call_type: str, 
        context_type: str, 
        context_id: str,
        participant_ids: List[str] = None
    ) -> Tuple[Optional[Call], Optional[str]]:
        """
        Initiate a new call.
        
        Args:
            initiator_id: ID of the user starting the call
            call_type: 'voice' or 'video'
            context_type: 'direct' or 'group'
            context_id: ID of the direct chat or group
            participant_ids: Optional list of participant IDs (for direct calls)
            
        Returns:
            Tuple of (Call, error_message)
        """
        if call_type not in ['voice', 'video']:
            return None, "Invalid call type. Must be 'voice' or 'video'"
        
        if context_type not in ['direct', 'group']:
            return None, "Invalid context type. Must be 'direct' or 'group'"
        
        # Validate context and get participants
        if context_type == 'direct':
            chat = DirectChat.query.get(context_id)
            if not chat:
                return None, "Chat not found"
            
            if chat.user1_id != initiator_id and chat.user2_id != initiator_id:
                return None, "Not authorized to start call in this chat"
            
            # Get the other participant
            other_user_id = chat.user2_id if chat.user1_id == initiator_id else chat.user1_id
            participant_ids = [other_user_id]
            
        else:  # group
            group = GroupLearning.query.get(context_id)
            if not group:
                return None, "Group not found"
            
            # Check if initiator is a member
            membership = GroupMember.query.filter_by(
                group_id=context_id,
                user_id=initiator_id,
                status='active'
            ).first()
            
            if not membership:
                return None, "Not a member of this group"
            
            # Get all active group members except initiator
            members = GroupMember.query.filter(
                GroupMember.group_id == context_id,
                GroupMember.status == 'active',
                GroupMember.user_id != initiator_id
            ).all()
            participant_ids = [m.user_id for m in members]
        
        # Check for existing active call in this context
        existing_call = Call.query.filter(
            Call.context_type == context_type,
            Call.context_id == context_id,
            Call.status.in_(['ringing', 'active'])
        ).first()
        
        if existing_call:
            return None, "There is already an active call in this context"
        
        # Create the call
        call = Call(
            initiator_id=initiator_id,
            call_type=call_type,
            context_type=context_type,
            context_id=context_id,
            status='ringing'
        )
        
        db.session.add(call)
        db.session.flush()  # Get the call ID
        
        # Add initiator as participant (already joined)
        initiator_participant = CallParticipant(
            call_id=call.id,
            user_id=initiator_id,
            status='joined',
            joined_at=datetime.utcnow()
        )
        db.session.add(initiator_participant)
        
        # Add other participants as invited
        for participant_id in participant_ids:
            participant = CallParticipant(
                call_id=call.id,
                user_id=participant_id,
                status='ringing'
            )
            db.session.add(participant)
        
        db.session.commit()
        
        return call, None
    
    def join_call(self, call_id: str, user_id: str) -> Tuple[Optional[CallParticipant], Optional[str]]:
        """
        Join an existing call.
        
        Args:
            call_id: The call's ID
            user_id: ID of the user joining
            
        Returns:
            Tuple of (CallParticipant, error_message)
        """
        call = Call.query.get(call_id)
        
        if not call:
            return None, "Call not found"
        
        if call.status not in ['ringing', 'active']:
            return None, "Call is no longer available"
        
        # Find participant record
        participant = CallParticipant.query.filter_by(
            call_id=call_id,
            user_id=user_id
        ).first()
        
        if not participant:
            return None, "Not invited to this call"
        
        if participant.status == 'joined':
            return participant, None  # Already joined
        
        if participant.status in ['left', 'declined']:
            return None, "Cannot rejoin this call"
        
        # Update participant status
        participant.status = 'joined'
        participant.joined_at = datetime.utcnow()
        
        # If this is the first person joining (besides initiator), start the call
        if call.status == 'ringing':
            call.status = 'active'
            call.started_at = datetime.utcnow()
        
        db.session.commit()
        
        return participant, None
    
    def leave_call(self, call_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Leave a call.
        
        Args:
            call_id: The call's ID
            user_id: ID of the user leaving
            
        Returns:
            Tuple of (success, error_message)
        """
        call = Call.query.get(call_id)
        
        if not call:
            return False, "Call not found"
        
        participant = CallParticipant.query.filter_by(
            call_id=call_id,
            user_id=user_id
        ).first()
        
        if not participant:
            return False, "Not a participant in this call"
        
        participant.status = 'left'
        participant.left_at = datetime.utcnow()
        
        # Check if call should end (no more active participants)
        active_participants = CallParticipant.query.filter_by(
            call_id=call_id,
            status='joined'
        ).count()
        
        if active_participants == 0:
            call.status = 'ended'
            call.ended_at = datetime.utcnow()
        
        db.session.commit()
        
        return True, None
    
    def decline_call(self, call_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Decline a call invitation.
        
        Args:
            call_id: The call's ID
            user_id: ID of the user declining
            
        Returns:
            Tuple of (success, error_message)
        """
        call = Call.query.get(call_id)
        
        if not call:
            return False, "Call not found"
        
        participant = CallParticipant.query.filter_by(
            call_id=call_id,
            user_id=user_id
        ).first()
        
        if not participant:
            return False, "Not invited to this call"
        
        if participant.status != 'ringing':
            return False, "Cannot decline - call status has changed"
        
        participant.status = 'declined'
        
        # For direct calls, if the only other participant declines, end the call
        if call.context_type == 'direct':
            call.status = 'declined'
            call.ended_at = datetime.utcnow()
        else:
            # For group calls, check if everyone declined
            pending = CallParticipant.query.filter(
                CallParticipant.call_id == call_id,
                CallParticipant.status.in_(['ringing', 'joined'])
            ).count()
            
            if pending == 0:
                call.status = 'declined'
                call.ended_at = datetime.utcnow()
        
        db.session.commit()
        
        return True, None
    
    def end_call(self, call_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        End a call (any participant can end).
        
        Args:
            call_id: The call's ID
            user_id: ID of the user ending the call
            
        Returns:
            Tuple of (success, error_message)
        """
        call = Call.query.get(call_id)
        
        if not call:
            return False, "Call not found"
        
        # Verify user is a participant
        participant = CallParticipant.query.filter_by(
            call_id=call_id,
            user_id=user_id
        ).first()
        
        if not participant:
            return False, "Not a participant in this call"
        
        if call.status == 'ended':
            return True, None  # Already ended
        
        call.status = 'ended'
        call.ended_at = datetime.utcnow()
        
        # Update all participants who were still in the call
        CallParticipant.query.filter(
            CallParticipant.call_id == call_id,
            CallParticipant.status == 'joined'
        ).update({'status': 'left', 'left_at': datetime.utcnow()})
        
        db.session.commit()
        
        return True, None
    
    def update_media_state(
        self, 
        call_id: str, 
        user_id: str, 
        is_muted: bool = None, 
        is_video_off: bool = None,
        is_screen_sharing: bool = None
    ) -> Tuple[Optional[CallParticipant], Optional[str]]:
        """
        Update media state for a participant.
        
        Args:
            call_id: The call's ID
            user_id: ID of the user
            is_muted: Whether audio is muted
            is_video_off: Whether video is off
            is_screen_sharing: Whether screen sharing is active
            
        Returns:
            Tuple of (CallParticipant, error_message)
        """
        participant = CallParticipant.query.filter_by(
            call_id=call_id,
            user_id=user_id,
            status='joined'
        ).first()
        
        if not participant:
            return None, "Not an active participant in this call"
        
        if is_muted is not None:
            participant.is_muted = is_muted
        if is_video_off is not None:
            participant.is_video_off = is_video_off
        if is_screen_sharing is not None:
            participant.is_screen_sharing = is_screen_sharing
        
        db.session.commit()
        
        return participant, None
    
    def get_call(self, call_id: str, user_id: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Get call details.
        
        Args:
            call_id: The call's ID
            user_id: Current user's ID (for authorization)
            
        Returns:
            Tuple of (call dict, error_message)
        """
        call = Call.query.get(call_id)
        
        if not call:
            return None, "Call not found"
        
        # Verify user is a participant
        participant = CallParticipant.query.filter_by(
            call_id=call_id,
            user_id=user_id
        ).first()
        
        if not participant:
            return None, "Not a participant in this call"
        
        return call.to_dict(include_participants=True), None
    
    def get_active_call(self, user_id: str) -> Optional[dict]:
        """
        Get the user's current active call if any.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Call dict or None
        """
        participant = CallParticipant.query.filter_by(
            user_id=user_id,
            status='joined'
        ).first()
        
        if not participant:
            return None
        
        call = Call.query.get(participant.call_id)
        if call and call.status == 'active':
            return call.to_dict(include_participants=True)
        
        return None
    
    def get_incoming_calls(self, user_id: str) -> List[dict]:
        """
        Get all incoming (ringing) calls for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of call dictionaries
        """
        participants = CallParticipant.query.filter_by(
            user_id=user_id,
            status='ringing'
        ).all()
        
        calls = []
        for participant in participants:
            call = Call.query.get(participant.call_id)
            if call and call.status == 'ringing':
                calls.append(call.to_dict(include_participants=True))
        
        return calls
    
    def timeout_call(self, call_id: str) -> Tuple[bool, Optional[str]]:
        """
        Mark a call as missed due to timeout.
        
        Args:
            call_id: The call's ID
            
        Returns:
            Tuple of (success, error_message)
        """
        call = Call.query.get(call_id)
        
        if not call:
            return False, "Call not found"
        
        if call.status != 'ringing':
            return False, "Call is not in ringing state"
        
        call.status = 'missed'
        call.ended_at = datetime.utcnow()
        
        db.session.commit()
        
        return True, None


# Singleton instance
call_service = CallService()
