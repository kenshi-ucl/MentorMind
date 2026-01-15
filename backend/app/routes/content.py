"""Content routes for file uploads and content management."""
from flask import Blueprint, request, jsonify
from app.services.content_service import content_service
from app.services.auth_service import auth_service
from app.routes.auth import require_auth

content_bp = Blueprint('content', __name__)


def get_current_user_id() -> tuple[str | None, dict | None, int | None]:
    """
    Get the current user ID from the authorization header.
    
    Returns:
        Tuple of (user_id, error_response, status_code).
        If successful, error_response and status_code are None.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, {'error': 'Not authenticated'}, 401
    
    token = auth_header.split(' ')[1]
    user = auth_service.get_user_by_session(token)
    
    if not user:
        return None, {'error': 'Session expired, please login again'}, 401
    
    return user.id, None, None


@content_bp.route('/upload', methods=['POST'])
@require_auth
def upload_content():
    """
    Upload a file (video or PDF).
    
    Headers:
        - Authorization: Bearer <token>
    
    Request:
        - multipart/form-data with 'file' field
    
    Returns:
        - 201: Content uploaded and processed successfully
        - 400: Invalid file type or missing file
        - 401: Not authenticated
        - 413: File too large
        - 500: Processing failed
    """
    # Get user from request context (set by require_auth decorator)
    user = request.current_user
    user_id = user.id
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type before reading
    is_valid, file_type, error = content_service.validate_file_type(file.filename)
    if not is_valid:
        return jsonify({'error': error}), 400
    
    try:
        # Read file data
        file_data = file.read()
        
        # Upload content
        content, error = content_service.upload_content(
            user_id=user_id,
            filename=file.filename,
            file_data=file_data
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        # Process content through ContentAgent
        processed_content, process_error = content_service.process_content(content.id)
        
        if process_error:
            # Content uploaded but processing failed
            return jsonify({
                'contentId': content.id,
                'filename': content.filename,
                'fileType': content.content_type,
                'warning': f'File uploaded but processing failed: {process_error}',
                'summary': '',
                'keyPoints': []
            }), 201
        
        return jsonify({
            'contentId': processed_content.id,
            'filename': processed_content.filename,
            'fileType': processed_content.content_type,
            'summary': processed_content.summary,
            'keyPoints': processed_content.key_points
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500


@content_bp.route('/list', methods=['GET'])
@require_auth
def list_contents():
    """
    List all content for the current user.
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: List of user's content
        - 401: Not authenticated
    """
    # Get user from request context (set by require_auth decorator)
    user = request.current_user
    user_id = user.id
    
    contents = content_service.get_user_content(user_id)
    
    return jsonify({
        'contents': [
            {
                'id': c.id,
                'filename': c.filename,
                'fileType': c.content_type,
                'title': c.title,
                'summary': c.summary,
                'keyPoints': c.key_points,
                'topics': c.topics,
                'processingStatus': c.processing_status,
                'createdAt': c.created_at.isoformat() if c.created_at else None
            }
            for c in contents
        ]
    }), 200


@content_bp.route('/<content_id>', methods=['GET'])
@require_auth
def get_content(content_id: str):
    """
    Get a specific content item.
    
    Headers:
        - Authorization: Bearer <token>
    
    Path Parameters:
        - content_id: ID of the content to retrieve
    
    Returns:
        - 200: Content details
        - 401: Not authenticated
        - 403: Not authorized
        - 404: Content not found
    """
    # Get user from request context (set by require_auth decorator)
    user = request.current_user
    user_id = user.id
    
    # Use user_id filter to ensure user can only access their own content
    content = content_service.get_content(content_id, user_id)
    
    if not content:
        # Check if content exists but belongs to another user
        content_exists = content_service.get_content(content_id)
        if content_exists:
            return jsonify({'error': 'Not authorized to access this content'}), 403
        return jsonify({'error': 'Content not found'}), 404
    
    return jsonify({
        'id': content.id,
        'filename': content.filename,
        'fileType': content.content_type,
        'title': content.title,
        'summary': content.summary,
        'keyPoints': content.key_points,
        'topics': content.topics,
        'processingStatus': content.processing_status,
        'createdAt': content.created_at.isoformat() if content.created_at else None
    }), 200


@content_bp.route('/<content_id>', methods=['DELETE'])
@require_auth
def delete_content(content_id: str):
    """
    Delete a content item.
    
    Headers:
        - Authorization: Bearer <token>
    
    Path Parameters:
        - content_id: ID of the content to delete
    
    Returns:
        - 200: Content deleted successfully
        - 401: Not authenticated
        - 403: Not authorized
        - 404: Content not found
    """
    # Get user from request context (set by require_auth decorator)
    user = request.current_user
    user_id = user.id
    
    success, error = content_service.delete_content(content_id, user_id)
    
    if not success:
        if "not found" in error.lower():
            return jsonify({'error': error}), 404
        if "not authorized" in error.lower():
            return jsonify({'error': error}), 403
        return jsonify({'error': error}), 500
    
    return jsonify({'message': 'Content deleted successfully'}), 200
