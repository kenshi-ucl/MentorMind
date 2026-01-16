"""Calls API routes for voice and video calls."""
from flask import Blueprint, request, jsonify
from app.services.call_service import call_service
from app.routes.auth import require_auth

calls_bp = Blueprint('calls', __name__)


@calls_bp.route('/initiate', methods=['POST'])
@require_auth
def initiate_call():
    """
    Initiate a new call.
    
    Request body:
        - callType: 'voice' or 'video'
        - contextType: 'direct' or 'group'
        - contextId: ID of the direct chat or group
    
    Returns:
        - 201: Call initiated
        - 400: Validation error
    """
    user = request.current_user
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    required_fields = ['callType', 'contextType', 'contextId']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    call, error = call_service.initiate_call(
        user.id,
        data['callType'],
        data['contextType'],
        data['contextId']
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(call.to_dict(include_participants=True)), 201


@calls_bp.route('/<call_id>/join', methods=['POST'])
@require_auth
def join_call(call_id):
    """
    Join an existing call.
    
    Returns:
        - 200: Joined successfully
        - 400: Validation error
        - 404: Call not found
    """
    user = request.current_user
    
    participant, error = call_service.join_call(call_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify(participant.to_dict()), 200


@calls_bp.route('/<call_id>/leave', methods=['POST'])
@require_auth
def leave_call(call_id):
    """
    Leave a call.
    
    Returns:
        - 200: Left successfully
        - 400: Validation error
        - 404: Call not found
    """
    user = request.current_user
    
    success, error = call_service.leave_call(call_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Left call successfully'}), 200


@calls_bp.route('/<call_id>/decline', methods=['POST'])
@require_auth
def decline_call(call_id):
    """
    Decline a call invitation.
    
    Returns:
        - 200: Declined successfully
        - 400: Validation error
        - 404: Call not found
    """
    user = request.current_user
    
    success, error, call_ended = call_service.decline_call(call_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Call declined', 'callEnded': call_ended}), 200


@calls_bp.route('/<call_id>/end', methods=['POST'])
@require_auth
def end_call(call_id):
    """
    End a call.
    
    Returns:
        - 200: Call ended
        - 400: Validation error
        - 404: Call not found
    """
    user = request.current_user
    
    success, error = call_service.end_call(call_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify({'message': 'Call ended'}), 200


@calls_bp.route('/<call_id>/media', methods=['PATCH'])
@require_auth
def update_media_state(call_id):
    """
    Update media state (mute, video, screen share).
    
    Request body:
        - isMuted: Boolean (optional)
        - isVideoOff: Boolean (optional)
        - isScreenSharing: Boolean (optional)
    
    Returns:
        - 200: Media state updated
        - 400: Validation error
        - 404: Call not found
    """
    user = request.current_user
    data = request.get_json() or {}
    
    participant, error = call_service.update_media_state(
        call_id,
        user.id,
        is_muted=data.get('isMuted'),
        is_video_off=data.get('isVideoOff'),
        is_screen_sharing=data.get('isScreenSharing')
    )
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify(participant.to_dict()), 200


@calls_bp.route('/<call_id>', methods=['GET'])
@require_auth
def get_call(call_id):
    """
    Get call details.
    
    Returns:
        - 200: Call details
        - 400: Not a participant
        - 404: Call not found
    """
    user = request.current_user
    
    call, error = call_service.get_call(call_id, user.id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 400
        return jsonify({'error': error}), status_code
    
    return jsonify(call), 200


@calls_bp.route('/active', methods=['GET'])
@require_auth
def get_active_call():
    """
    Get the current user's active call if any.
    
    Returns:
        - 200: Active call or null
    """
    user = request.current_user
    call = call_service.get_active_call(user.id)
    
    return jsonify({'call': call}), 200


@calls_bp.route('/incoming', methods=['GET'])
@require_auth
def get_incoming_calls():
    """
    Get all incoming (ringing) calls.
    
    Returns:
        - 200: List of incoming calls
    """
    user = request.current_user
    calls = call_service.get_incoming_calls(user.id)
    
    return jsonify({'calls': calls}), 200


@calls_bp.route('/cleanup/<context_type>/<context_id>', methods=['POST'])
@require_auth
def cleanup_stale_calls(context_type, context_id):
    """
    Clean up any stale/stuck calls in a context.
    This is useful when calls get stuck due to network issues or crashes.
    
    Returns:
        - 200: Cleanup completed
        - 400: Invalid context type
    """
    user = request.current_user
    
    if context_type not in ['direct', 'group']:
        return jsonify({'error': 'Invalid context type'}), 400
    
    cleaned_count = call_service.cleanup_stale_calls(context_type, context_id, user.id)
    
    return jsonify({
        'message': f'Cleaned up {cleaned_count} stale call(s)',
        'cleanedCount': cleaned_count
    }), 200
