"""Authentication routes for user registration, login, and anonymous sessions."""
from functools import wraps
from flask import Blueprint, request, jsonify
from app.services.auth_service import auth_service
from app.errors import db_error_handler

auth_bp = Blueprint('auth', __name__)


def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    Validates the Authorization header and sets request.current_user.
    Returns 401 if authentication fails.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        user = auth_service.validate_token(token)
        
        if not user:
            return jsonify({'error': 'Session expired, please login again'}), 401
        
        # Store user in request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
@db_error_handler
def register():
    """
    Register a new user.
    
    Request body:
        - email: str (required)
        - password: str (required, min 6 characters)
        - name: str (required)
    
    Returns:
        - 201: User created successfully with user data and token
        - 400: Missing required fields or validation error
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
    
    # Use the new database-backed register method
    result, error = auth_service.register(email, password, name)
    
    if error:
        if "already exists" in error:
            return jsonify({'error': error}), 409
        return jsonify({'error': error}), 400
    
    user = result['user']
    session = result['session']
    
    return jsonify({
        'user': user.to_dict(),
        'token': session.token
    }), 201


@auth_bp.route('/login', methods=['POST'])
@db_error_handler
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
    
    # Use the new database-backed login method
    result, error = auth_service.login(email, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    user = result['user']
    session = result['session']
    
    return jsonify({
        'user': user.to_dict(),
        'token': session.token
    }), 200


@auth_bp.route('/anonymous', methods=['POST'])
@db_error_handler
def anonymous_session():
    """
    Create an anonymous user session.
    
    Returns:
        - 200: Anonymous session created with session ID and user data
    """
    # Use the new database-backed create_anonymous method
    result = auth_service.create_anonymous()
    user = result['user']
    session = result['session']
    
    return jsonify({
        'sessionId': session.token,
        'token': session.token,
        'isAnonymous': True,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@db_error_handler
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
    
    # Use the new database-backed logout method
    if auth_service.logout(token):
        return jsonify({'message': 'Logged out successfully'}), 200
    
    return jsonify({'error': 'No valid session'}), 401


@auth_bp.route('/me', methods=['GET'])
@db_error_handler
def get_current_user():
    """
    Get the current authenticated user.
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: User data
        - 401: Not authenticated or session expired
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Use the new database-backed validate_token method
    user = auth_service.validate_token(token)
    
    if not user:
        return jsonify({'error': 'Session expired, please login again'}), 401
    
    return jsonify({'user': user.to_dict()}), 200
