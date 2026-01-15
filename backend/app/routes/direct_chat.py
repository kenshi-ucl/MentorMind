"""Direct chat API routes for messaging between friends."""
from flask import Blueprint, request, jsonify
from app.services.chat_service import chat_service
from app.routes.auth import require_auth

direct_chat_bp = Blueprint('direct_chat', __name__)


@direct_chat_bp.route('/direct/<friend_id>', methods=['GET'])
@require_auth
def get_or_create_direct_chat(friend_id):
    """
    Get or create a direct chat with a friend.
    
    Returns:
        - 200: Direct chat object
        - 400: Validation error
    """
    user = request.current_user
    
    chat, error = chat_service.get_or_create_direct_chat(user.id, friend_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(chat.to_dict(current_user_id=user.id)), 200


@direct_chat_bp.route('/direct', methods=['GET'])
@require_auth
def get_user_chats():
    """
    Get all direct chats for the current user.
    
    Returns:
        - 200: List of direct chats
    """
    user = request.current_user
    chats = chat_service.get_user_chats(user.id)
    
    return jsonify({'chats': chats}), 200


@direct_chat_bp.route('/<chat_id>/messages', methods=['GET'])
@require_auth
def get_messages(chat_id):
    """
    Get messages for a chat with pagination.
    
    Query params:
        - limit: Maximum messages (default 50)
        - offset: Number to skip (default 0)
    
    Returns:
        - 200: List of messages
        - 400: Validation error
        - 404: Chat not found
    """
    user = request.current_user
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    messages, error = chat_service.get_messages(chat_id, user.id, limit, offset)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'messages': messages}), 200


@direct_chat_bp.route('/<chat_id>/messages', methods=['POST'])
@require_auth
def send_message(chat_id):
    """
    Send a message in a direct chat.
    
    Request body:
        - content: Message content (required)
    
    Returns:
        - 201: Message sent
        - 400: Validation error
        - 404: Chat not found
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    
    message, error = chat_service.send_message(chat_id, user.id, data['content'])
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify(message.to_dict()), 201


@direct_chat_bp.route('/<chat_id>/read', methods=['POST'])
@require_auth
def mark_as_read(chat_id):
    """
    Mark messages as read.
    
    Request body:
        - messageIds: Optional list of specific message IDs (marks all if omitted)
    
    Returns:
        - 200: Messages marked as read
        - 400: Validation error
        - 404: Chat not found
    """
    user = request.current_user
    data = request.get_json() or {}
    message_ids = data.get('messageIds')
    
    count, error = chat_service.mark_as_read(chat_id, user.id, message_ids)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'markedAsRead': count}), 200
