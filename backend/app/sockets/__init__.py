"""
WebSocket event handlers for real-time communication.
"""
import logging
from datetime import datetime
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from app.services.presence_service import presence_service
from app.services.auth_service import auth_service
from app.services.chat_service import chat_service
from app.services.call_service import call_service
from app.database import db

logger = logging.getLogger(__name__)

# SocketIO instance - will be initialized in create_app
socketio = SocketIO()


def init_socketio(app):
    """Initialize SocketIO with the Flask app."""
    socketio.init_app(
        app,
        cors_allowed_origins=["http://localhost:5173", "http://localhost:5174"],
        async_mode='eventlet',
        logger=True,
        engineio_logger=True
    )
    return socketio


def get_user_from_token(token):
    """Get user from authentication token."""
    if not token:
        return None
    return auth_service.get_user_by_session(token)


# Connection handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        logger.warning("WebSocket connection rejected - invalid token")
        return False
    
    # Set user online
    presence_service.set_online(user.id, request.sid)
    
    # Join user's personal room for direct messages
    join_room(f"user:{user.id}")
    
    # Notify friends that user is online
    from app.models.friend import Friend
    friendships = Friend.query.filter_by(user_id=user.id).all()
    for friendship in friendships:
        emit('presence:online', {
            'userId': user.id,
            'userName': user.name
        }, room=f"user:{friendship.friend_id}")
    
    logger.info(f"User {user.id} connected via WebSocket")
    return True


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if user:
        # Set user offline
        presence_service.set_offline(user.id)
        
        # Leave user's personal room
        leave_room(f"user:{user.id}")
        
        # Notify friends that user is offline
        from app.models.friend import Friend
        friendships = Friend.query.filter_by(user_id=user.id).all()
        for friendship in friendships:
            emit('presence:offline', {
                'userId': user.id,
                'lastSeen': datetime.utcnow().isoformat()
            }, room=f"user:{friendship.friend_id}")
        
        logger.info(f"User {user.id} disconnected from WebSocket")


# Chat event handlers
@socketio.on('chat:join')
def handle_chat_join(data):
    """Join a chat room."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        logger.warning("chat:join - Unauthorized user")
        return {'error': 'Unauthorized'}
    
    chat_id = data.get('chatId')
    chat_type = data.get('chatType', 'direct')  # 'direct' or 'group'
    
    if not chat_id:
        logger.warning("chat:join - Missing chatId")
        return {'error': 'chatId is required'}
    
    room = f"{chat_type}:{chat_id}"
    join_room(room)
    
    logger.info(f"User {user.id} joined chat room {room}")
    return {'success': True, 'room': room}


@socketio.on('chat:leave')
def handle_chat_leave(data):
    """Leave a chat room."""
    chat_id = data.get('chatId')
    chat_type = data.get('chatType', 'direct')
    
    if chat_id:
        room = f"{chat_type}:{chat_id}"
        leave_room(room)


@socketio.on('chat:message')
def handle_chat_message(data):
    """Handle sending a chat message."""
    logger.info(f"Received chat:message event with data: {data}")
    
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        logger.warning("chat:message - Unauthorized user")
        return {'error': 'Unauthorized'}
    
    chat_id = data.get('chatId')
    content = data.get('content')
    chat_type = data.get('chatType', 'direct')
    
    logger.info(f"chat:message - user={user.id}, chat_id={chat_id}, chat_type={chat_type}")
    
    if not chat_id or not content:
        logger.warning("chat:message - Missing chatId or content")
        return {'error': 'chatId and content are required'}
    
    # Save message to database
    if chat_type == 'direct':
        message, error = chat_service.send_message(chat_id, user.id, content)
    else:
        from app.services.group_service import group_service
        message, error = group_service.send_group_message(chat_id, user.id, content)
    
    if error:
        logger.error(f"chat:message - Error: {error}")
        return {'error': error}
    
    logger.info(f"chat:message - Message saved: {message.id}")
    
    # Broadcast to chat room
    room = f"{chat_type}:{chat_id}"
    emit('chat:message', message.to_dict(), room=room, include_self=False)
    
    result = {'success': True, 'message': message.to_dict()}
    logger.info(f"chat:message - Returning: {result}")
    return result


@socketio.on('chat:typing')
def handle_typing(data):
    """Handle typing indicator."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    chat_id = data.get('chatId')
    chat_type = data.get('chatType', 'direct')
    is_typing = data.get('isTyping', True)
    
    if chat_id:
        room = f"{chat_type}:{chat_id}"
        emit('chat:typing', {
            'userId': user.id,
            'userName': user.name,
            'isTyping': is_typing
        }, room=room, include_self=False)


@socketio.on('chat:read')
def handle_read(data):
    """Handle marking messages as read."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    chat_id = data.get('chatId')
    message_ids = data.get('messageIds')
    chat_type = data.get('chatType', 'direct')
    
    if chat_id:
        if chat_type == 'direct':
            chat_service.mark_as_read(chat_id, user.id, message_ids)
        
        room = f"{chat_type}:{chat_id}"
        emit('chat:read', {
            'userId': user.id,
            'messageIds': message_ids
        }, room=room, include_self=False)


# Call signaling event handlers
@socketio.on('call:initiate')
def handle_call_initiate(data):
    """Handle call initiation."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return {'error': 'Unauthorized'}
    
    call_type = data.get('callType')
    context_type = data.get('contextType')
    context_id = data.get('contextId')
    
    logger.info(f"Call initiate: user={user.id}, type={call_type}, context={context_type}:{context_id}")
    
    call, error = call_service.initiate_call(
        user.id, call_type, context_type, context_id
    )
    
    if error:
        logger.error(f"Call initiate error: {error}")
        return {'error': error}
    
    # Join call room as initiator
    join_room(f"call:{call.id}")
    logger.info(f"User {user.id} joined call room call:{call.id}")
    
    # Notify all participants
    for participant in call.participants.all():
        if participant.user_id != user.id:
            logger.info(f"Sending ring to user:{participant.user_id}")
            emit('call:ring', call.to_dict(include_participants=True), 
                 room=f"user:{participant.user_id}")
    
    return {'success': True, 'call': call.to_dict(include_participants=True)}


@socketio.on('call:accept')
def handle_call_accept(data):
    """Handle accepting a call."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return {'error': 'Unauthorized'}
    
    call_id = data.get('callId')
    
    logger.info(f"Call accept: user={user.id}, call={call_id}")
    
    participant, error = call_service.join_call(call_id, user.id)
    
    if error:
        logger.error(f"Call accept error: {error}")
        return {'error': error}
    
    # Join call room
    join_room(f"call:{call_id}")
    logger.info(f"User {user.id} joined call room call:{call_id}")
    
    # Get the call to find the initiator
    from app.models.call import Call
    call = Call.query.get(call_id)
    
    # Notify other participants (including the initiator who is already in the room)
    logger.info(f"Sending call:accepted to room call:{call_id}")
    emit('call:accepted', {
        'callId': call_id,
        'userId': user.id,
        'userName': user.name
    }, room=f"call:{call_id}", include_self=False)
    
    # Also send directly to the initiator's user room to ensure delivery
    if call and call.initiator_id != user.id:
        logger.info(f"Also sending call:accepted directly to initiator user:{call.initiator_id}")
        emit('call:accepted', {
            'callId': call_id,
            'userId': user.id,
            'userName': user.name
        }, room=f"user:{call.initiator_id}")
    
    return {'success': True, 'participant': participant.to_dict()}


@socketio.on('call:decline')
def handle_call_decline(data):
    """Handle declining a call."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return {'error': 'Unauthorized'}
    
    call_id = data.get('callId')
    
    success, error = call_service.decline_call(call_id, user.id)
    
    if error:
        return {'error': error}
    
    # Notify other participants
    emit('call:declined', {
        'callId': call_id,
        'userId': user.id
    }, room=f"call:{call_id}")
    
    return {'success': True}


@socketio.on('call:offer')
def handle_call_offer(data):
    """Handle WebRTC offer."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    call_id = data.get('callId')
    target_user_id = data.get('targetUserId')
    offer = data.get('offer')
    
    logger.info(f"Call offer: from={user.id}, to={target_user_id}, call={call_id}")
    
    emit('call:offer', {
        'callId': call_id,
        'fromUserId': user.id,
        'offer': offer
    }, room=f"user:{target_user_id}")


@socketio.on('call:answer')
def handle_call_answer(data):
    """Handle WebRTC answer."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    call_id = data.get('callId')
    target_user_id = data.get('targetUserId')
    answer = data.get('answer')
    
    logger.info(f"Call answer: from={user.id}, to={target_user_id}, call={call_id}")
    
    emit('call:answer', {
        'callId': call_id,
        'fromUserId': user.id,
        'answer': answer
    }, room=f"user:{target_user_id}")


@socketio.on('call:ice-candidate')
def handle_ice_candidate(data):
    """Handle ICE candidate exchange."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    call_id = data.get('callId')
    target_user_id = data.get('targetUserId')
    candidate = data.get('candidate')
    
    logger.info(f"ICE candidate: from={user.id}, to={target_user_id}, call={call_id}")
    
    emit('call:ice-candidate', {
        'callId': call_id,
        'fromUserId': user.id,
        'candidate': candidate
    }, room=f"user:{target_user_id}")


@socketio.on('call:end')
def handle_call_end(data):
    """Handle ending a call."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return {'error': 'Unauthorized'}
    
    call_id = data.get('callId')
    
    success, error = call_service.end_call(call_id, user.id)
    
    if error:
        return {'error': error}
    
    # Notify all participants
    emit('call:ended', {
        'callId': call_id,
        'endedBy': user.id
    }, room=f"call:{call_id}")
    
    # Leave call room
    leave_room(f"call:{call_id}")
    
    return {'success': True}


@socketio.on('call:media-state')
def handle_media_state(data):
    """Handle media state changes (mute, video, screen share)."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    call_id = data.get('callId')
    
    participant, error = call_service.update_media_state(
        call_id,
        user.id,
        is_muted=data.get('isMuted'),
        is_video_off=data.get('isVideoOff'),
        is_screen_sharing=data.get('isScreenSharing')
    )
    
    if not error:
        emit('call:media-state', {
            'callId': call_id,
            'userId': user.id,
            'isMuted': participant.is_muted,
            'isVideoOff': participant.is_video_off,
            'isScreenSharing': participant.is_screen_sharing
        }, room=f"call:{call_id}", include_self=False)


# Presence event handlers
@socketio.on('presence:status')
def handle_presence_status(data):
    """Handle presence status update."""
    token = request.args.get('token')
    user = get_user_from_token(token)
    
    if not user:
        return
    
    status = data.get('status', 'available')
    presence_service.set_status(user.id, status)
    
    # Notify friends
    from app.models.friend import Friend
    friendships = Friend.query.filter_by(user_id=user.id).all()
    for friendship in friendships:
        emit('presence:status', {
            'userId': user.id,
            'status': status
        }, room=f"user:{friendship.friend_id}")
