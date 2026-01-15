"""Groups API routes for managing group learning sessions."""
from flask import Blueprint, request, jsonify
from app.services.group_service import group_service
from app.routes.auth import require_auth

groups_bp = Blueprint('groups', __name__)


@groups_bp.route('', methods=['POST'])
@require_auth
def create_group():
    """
    Create a new group learning session.
    
    Request body:
        - name: Group name (required)
        - description: Optional description
    
    Returns:
        - 201: Group created
        - 400: Validation error
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    
    group, error = group_service.create_group(
        user.id,
        data['name'],
        data.get('description')
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(group.to_dict(include_members=True)), 201


@groups_bp.route('', methods=['GET'])
@require_auth
def get_user_groups():
    """
    Get all groups the current user is a member of.
    
    Returns:
        - 200: List of groups
    """
    user = request.current_user
    groups = group_service.get_user_groups(user.id)
    
    return jsonify({'groups': groups}), 200


@groups_bp.route('/<group_id>', methods=['GET'])
@require_auth
def get_group(group_id):
    """
    Get group details.
    
    Returns:
        - 200: Group details with members
        - 400: Not a member
        - 404: Group not found
    """
    user = request.current_user
    
    group, error = group_service.get_group(group_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify(group), 200


@groups_bp.route('/<group_id>/invite', methods=['POST'])
@require_auth
def invite_to_group(group_id):
    """
    Invite friends to a group.
    
    Request body:
        - userIds: List of user IDs to invite
    
    Returns:
        - 200: Invitation results
        - 400: Validation error
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or not data.get('userIds'):
        return jsonify({'error': 'userIds is required'}), 400
    
    if not isinstance(data['userIds'], list):
        return jsonify({'error': 'userIds must be a list'}), 400
    
    successful, failed = group_service.invite_to_group(
        group_id,
        user.id,
        data['userIds']
    )
    
    return jsonify({
        'invited': successful,
        'failed': failed
    }), 200


@groups_bp.route('/<group_id>/join', methods=['POST'])
@require_auth
def join_group(group_id):
    """
    Accept a group invitation and join.
    
    Returns:
        - 200: Joined successfully
        - 400: Validation error
        - 404: Invitation not found
    """
    user = request.current_user
    
    success, error = group_service.join_group(group_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Joined group successfully'}), 200


@groups_bp.route('/<group_id>/leave', methods=['POST'])
@require_auth
def leave_group(group_id):
    """
    Leave a group.
    
    Returns:
        - 200: Left successfully
        - 400: Validation error
    """
    user = request.current_user
    
    success, error = group_service.leave_group(group_id, user.id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({'message': 'Left group successfully'}), 200


@groups_bp.route('/<group_id>/decline', methods=['POST'])
@require_auth
def decline_invitation(group_id):
    """
    Decline a group invitation.
    
    Returns:
        - 200: Declined successfully
        - 400: Validation error
        - 404: Invitation not found
    """
    user = request.current_user
    
    success, error = group_service.decline_invitation(group_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Invitation declined'}), 200


@groups_bp.route('/<group_id>/members/<member_id>', methods=['DELETE'])
@require_auth
def remove_member(group_id, member_id):
    """
    Remove a member from the group (creator only).
    
    Returns:
        - 200: Member removed
        - 400: Not authorized or validation error
        - 404: Member not found
    """
    user = request.current_user
    
    success, error = group_service.remove_member(group_id, user.id, member_id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Member removed'}), 200


@groups_bp.route('/<group_id>/members', methods=['GET'])
@require_auth
def get_group_members(group_id):
    """
    Get all members of a group.
    
    Returns:
        - 200: List of members
        - 400: Not a member
        - 404: Group not found
    """
    user = request.current_user
    
    group, error = group_service.get_group(group_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'members': group.get('members', [])}), 200


@groups_bp.route('/invitations', methods=['GET'])
@require_auth
def get_pending_invitations():
    """
    Get all pending group invitations for the current user.
    
    Returns:
        - 200: List of pending invitations
    """
    user = request.current_user
    invitations = group_service.get_pending_invitations(user.id)
    
    return jsonify({'invitations': invitations}), 200


@groups_bp.route('/<group_id>/messages', methods=['GET'])
@require_auth
def get_group_messages(group_id):
    """
    Get messages for a group with pagination.
    
    Query params:
        - limit: Maximum messages (default 50)
        - offset: Number to skip (default 0)
    
    Returns:
        - 200: List of messages
        - 400: Not a member
        - 404: Group not found
    """
    user = request.current_user
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    messages, error = group_service.get_group_messages(group_id, user.id, limit, offset)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'messages': messages}), 200


@groups_bp.route('/<group_id>/messages', methods=['POST'])
@require_auth
def send_group_message(group_id):
    """
    Send a message in a group.
    
    Request body:
        - content: Message content (required)
    
    Returns:
        - 201: Message sent
        - 400: Validation error
        - 404: Group not found
    """
    user = request.current_user
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    
    message, error = group_service.send_group_message(group_id, user.id, data['content'])
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify(message.to_dict()), 201
