"""
Authentication decorators for protecting routes.

Provides decorators for validating user authentication on protected endpoints.
"""
from functools import wraps
from flask import request, jsonify, g
from app.services.auth_service import auth_service


def require_auth(f):
    """
    Decorator to require authentication for a route.
    
    Validates the Authorization header contains a valid Bearer token.
    If valid, sets g.current_user to the authenticated user.
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user = g.current_user
            return jsonify({'user': user.to_dict()})
    
    Returns:
        - 401 Unauthorized if:
            - Authorization header is missing
            - Authorization header doesn't start with 'Bearer '
            - Token is invalid or expired
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # Check if Authorization header exists
        if not auth_header:
            return jsonify({
                'error': 'Authorization required',
                'code': 'MISSING_AUTH_HEADER'
            }), 401
        
        # Check if it's a Bearer token
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Invalid authorization format. Use: Bearer <token>',
                'code': 'INVALID_AUTH_FORMAT'
            }), 401
        
        # Extract the token
        token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'error': 'Token is required',
                'code': 'MISSING_TOKEN'
            }), 401
        
        # Validate the token and get the user
        user = auth_service.validate_token(token)
        
        if not user:
            return jsonify({
                'error': 'Session expired or invalid. Please login again.',
                'code': 'INVALID_TOKEN'
            }), 401
        
        # Store the current user in Flask's g object for access in the route
        g.current_user = user
        g.auth_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Decorator for routes that optionally accept authentication.
    
    If a valid token is provided, sets g.current_user to the authenticated user.
    If no token or invalid token, g.current_user will be None.
    The route will still execute either way.
    
    Usage:
        @app.route('/public-or-private')
        @optional_auth
        def public_or_private_route():
            user = g.current_user  # May be None
            if user:
                return jsonify({'message': f'Hello, {user.name}!'})
            return jsonify({'message': 'Hello, guest!'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.current_user = None
        g.auth_token = None
        
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            if token:
                user = auth_service.validate_token(token)
                if user:
                    g.current_user = user
                    g.auth_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function
