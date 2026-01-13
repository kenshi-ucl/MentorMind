"""Progress routes for user learning progress tracking."""
from flask import Blueprint, request, jsonify
from app.services.progress_service import progress_service
from app.services.auth_service import auth_service

progress_bp = Blueprint('progress', __name__)


def get_current_user_id() -> tuple[str | None, dict | None, int | None]:
    """
    Get the current user ID from the authorization header.
    
    Returns:
        Tuple of (user_id, error_response, status_code).
        If successful, error_response and status_code are None.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None, {'error': 'Authorization header required'}, 401
    
    # Handle both "Bearer <token>" and just "<token>" formats
    token = auth_header
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    # Validate token and get user
    user = auth_service.validate_token(token)
    if not user:
        return None, {'error': 'Invalid or expired token'}, 401
    
    return user.id, None, None


@progress_bp.route('', methods=['GET'])
def get_progress():
    """
    Get user progress data.
    
    Returns progress metrics including:
    - Total quizzes taken
    - Overall success rate
    - Topics mastered (>= 80% success rate)
    - Topics needing improvement (< 50% success rate)
    - Progress over time
    
    Returns:
        - 200: Progress data
        - 401: Unauthorized
    """
    user_id, error, status = get_current_user_id()
    if error:
        return jsonify(error), status
    
    progress = progress_service.get_user_progress(user_id)
    
    return jsonify({
        'progressData': progress.to_dict()
    }), 200
