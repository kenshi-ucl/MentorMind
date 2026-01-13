"""Authentication routes for user registration, login, and anonymous sessions."""
from flask import Blueprint, request, jsonify
from app.services.auth_service import auth_service

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Request body:
        - email: str (required)
        - password: str (required, min 6 characters)
        - name: str (required)
    
    Returns:
        - 201: User created successfully with user data and token
        - 400: Missing required fields
        - 409: Email already exists
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    # Validate required fields
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    user, error = auth_service.register(email, password, name)
    
    if error:
        if "already exists" in error:
            return jsonify({'error': error}), 409
        return jsonify({'error': error}), 400
    
    # Create session token
    token = auth_service.create_session(user.id)
    
    return jsonify({
        'user': user.to_dict(),
        'token': token
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user with email and password.
    
    Request body:
        - email: str (required)
        - password: str (required)
    
    Returns:
        - 200: Login successful with user data and token
        - 400: Missing required fields
        - 401: Invalid credentials
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    user, error = auth_service.login(email, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    # Create session token
    token = auth_service.create_session(user.id)
    
    return jsonify({
        'user': user.to_dict(),
        'token': token
    }), 200


@auth_bp.route('/anonymous', methods=['POST'])
def anonymous_session():
    """
    Create an anonymous user session.
    
    Returns:
        - 200: Anonymous session created with session ID
    """
    session_id, user = auth_service.create_anonymous_session()
    
    return jsonify({
        'sessionId': session_id,
        'isAnonymous': True,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout and invalidate the current session.
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: Logout successful
        - 401: No valid session
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No valid session'}), 401
    
    token = auth_header.split(' ')[1]
    
    if auth_service.invalidate_session(token):
        return jsonify({'message': 'Logged out successfully'}), 200
    
    return jsonify({'error': 'No valid session'}), 401


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get the current authenticated user.
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: User data
        - 401: Not authenticated
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = auth_header.split(' ')[1]
    user = auth_service.get_user_by_session(token)
    
    if not user:
        return jsonify({'error': 'Session expired, please login again'}), 401
    
    return jsonify({'user': user.to_dict()}), 200
