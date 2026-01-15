"""Friends API routes for managing friendships and friend requests."""
from flask import Blueprint, request, jsonify
from app.services.friend_service import friend_service
from app.services.presence_service import presence_service
from app.routes.auth import require_auth

friends_bp = Blueprint('friends', __name__)


@friends_bp.route('', methods=['GET'])
@require_auth
def get_friends():
    """
    Get all friends for the current user.
    
    Returns:
        - 200: List of friends with online status
    """
    user = request.current_user
    friends = friend_service.get_friends(user.id)
    
    # Add online status to each friend
    presences = presence_service.get_friends_presence(user.id)
    presence_map = {p['userId']: p for p in presences}
    
    for friend in friends:
        presence = presence_map.get(friend['id'], {})
        friend['isOnline'] = presence.get('isOnline', False)
        friend['lastSeen'] = presence.get('lastSeen')
        friend['status'] = presence.get('status', 'available')
    
    return jsonify({'friends': friends}), 200


@friends_bp.route('/search', methods=['GET'])
@require_auth
def search_users():
    """
    Search for users by name or email.
    
    Query params:
        - q: Search query (required, min 2 characters)
        - limit: Maximum results (optional, default 20)
    
    Returns:
        - 200: List of matching users
        - 400: Missing or invalid query
    """
    user = request.current_user
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if len(query) < 2:
        return jsonify({'error': 'Search query must be at least 2 characters'}), 400
    
    users = friend_service.search_users(query, user.id, limit)
    
    return jsonify({'users': users}), 200


@friends_bp.route('/request', methods=['POST'])
@require_auth
def send_friend_request():
    """
    Send a friend request.
    
    Request body:
        - recipientId: ID of the user to send request to
    
    Returns:
        - 201: Friend request sent
        - 400: Invalid request or validation error
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or not data.get('recipientId'):
        return jsonify({'error': 'recipientId is required'}), 400
    
    friend_request, error = friend_service.send_friend_request(
        user.id, 
        data['recipientId']
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(friend_request.to_dict(include_users=True)), 201


@friends_bp.route('/requests', methods=['GET'])
@require_auth
def get_pending_requests():
    """
    Get all pending friend requests for the current user.
    
    Query params:
        - type: 'received' (default) or 'sent'
    
    Returns:
        - 200: List of pending friend requests
    """
    user = request.current_user
    request_type = request.args.get('type', 'received')
    
    if request_type == 'sent':
        requests = friend_service.get_sent_requests(user.id)
    else:
        requests = friend_service.get_pending_requests(user.id)
    
    return jsonify({'requests': requests}), 200


@friends_bp.route('/requests/<request_id>/accept', methods=['POST'])
@require_auth
def accept_friend_request(request_id):
    """
    Accept a friend request.
    
    Returns:
        - 200: Friend request accepted
        - 400: Invalid request
        - 404: Request not found
    """
    user = request.current_user
    
    success, error = friend_service.accept_request(request_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Friend request accepted'}), 200


@friends_bp.route('/requests/<request_id>/decline', methods=['POST'])
@require_auth
def decline_friend_request(request_id):
    """
    Decline a friend request.
    
    Returns:
        - 200: Friend request declined
        - 400: Invalid request
        - 404: Request not found
    """
    user = request.current_user
    
    success, error = friend_service.decline_request(request_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Friend request declined'}), 200


@friends_bp.route('/<friend_id>', methods=['DELETE'])
@require_auth
def remove_friend(friend_id):
    """
    Remove a friend.
    
    Returns:
        - 200: Friend removed
        - 404: Friendship not found
    """
    user = request.current_user
    
    success, error = friend_service.remove_friend(user.id, friend_id)
    
    if error:
        return jsonify({'error': error}), 404
    
    return jsonify({'message': 'Friend removed'}), 200


@friends_bp.route('/presence', methods=['GET'])
@require_auth
def get_friends_presence():
    """
    Get online status of all friends.
    
    Returns:
        - 200: List of friend presence statuses
    """
    user = request.current_user
    presences = presence_service.get_friends_presence(user.id)
    
    return jsonify({'presences': presences}), 200
