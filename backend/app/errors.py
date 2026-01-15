"""
Error handling module for database operations.

Provides centralized error handling for database-related errors,
returning appropriate HTTP status codes and user-friendly messages.
"""
import logging
from functools import wraps
from flask import jsonify
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    DatabaseError,
    TimeoutError as SQLTimeoutError
)

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(Exception):
    """Raised when a database query fails."""
    pass


class DatabaseTransactionError(Exception):
    """Raised when a database transaction fails."""
    pass


def handle_database_error(error: Exception) -> tuple:
    """
    Handle database errors and return appropriate HTTP response.
    
    Args:
        error: The exception that occurred
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    # Log the error for debugging
    logger.error(f"Database error: {type(error).__name__}: {str(error)}")
    
    if isinstance(error, OperationalError):
        # Connection errors, database unavailable
        logger.error(f"Database connection error: {error}")
        return {
            'error': 'Database service is temporarily unavailable. Please try again later.',
            'code': 'DATABASE_UNAVAILABLE'
        }, 503
    
    if isinstance(error, IntegrityError):
        # Constraint violations (unique, foreign key, etc.)
        error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)
        
        if 'UNIQUE constraint' in error_msg or 'unique' in error_msg.lower():
            return {
                'error': 'A record with this information already exists.',
                'code': 'DUPLICATE_ENTRY'
            }, 409
        
        if 'FOREIGN KEY constraint' in error_msg or 'foreign key' in error_msg.lower():
            return {
                'error': 'Referenced record does not exist.',
                'code': 'INVALID_REFERENCE'
            }, 400
        
        return {
            'error': 'Data integrity error. Please check your input.',
            'code': 'INTEGRITY_ERROR'
        }, 400
    
    if isinstance(error, SQLTimeoutError):
        # Query timeout
        logger.error(f"Database timeout: {error}")
        return {
            'error': 'Request timed out. Please try again.',
            'code': 'DATABASE_TIMEOUT'
        }, 504
    
    if isinstance(error, DatabaseError):
        # General database errors
        logger.error(f"Database error: {error}")
        return {
            'error': 'A database error occurred. Please try again later.',
            'code': 'DATABASE_ERROR'
        }, 500
    
    if isinstance(error, SQLAlchemyError):
        # Catch-all for SQLAlchemy errors
        logger.error(f"SQLAlchemy error: {error}")
        return {
            'error': 'An unexpected database error occurred.',
            'code': 'SQLALCHEMY_ERROR'
        }, 500
    
    # Unknown error
    logger.error(f"Unknown error: {error}")
    return {
        'error': 'An unexpected error occurred.',
        'code': 'UNKNOWN_ERROR'
    }, 500


def db_error_handler(f):
    """
    Decorator to handle database errors in route handlers.
    
    Wraps a route function and catches database-related exceptions,
    returning appropriate HTTP responses.
    
    Usage:
        @app.route('/api/users')
        @db_error_handler
        def get_users():
            # Database operations here
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (SQLAlchemyError, DatabaseConnectionError, 
                DatabaseQueryError, DatabaseTransactionError) as e:
            response, status_code = handle_database_error(e)
            return jsonify(response), status_code
    return decorated_function


def safe_commit(db_session):
    """
    Safely commit a database session with error handling.
    
    Args:
        db_session: SQLAlchemy database session
        
    Raises:
        DatabaseTransactionError: If commit fails
    """
    try:
        db_session.commit()
    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(f"Transaction commit failed: {e}")
        raise DatabaseTransactionError(f"Failed to save changes: {str(e)}")


def safe_rollback(db_session):
    """
    Safely rollback a database session.
    
    Args:
        db_session: SQLAlchemy database session
    """
    try:
        db_session.rollback()
    except SQLAlchemyError as e:
        logger.error(f"Rollback failed: {e}")


def register_error_handlers(app):
    """
    Register global error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        """Handle SQLAlchemy errors globally."""
        response, status_code = handle_database_error(error)
        return jsonify(response), status_code
    
    @app.errorhandler(DatabaseConnectionError)
    def handle_connection_error(error):
        """Handle database connection errors."""
        logger.error(f"Database connection error: {error}")
        return jsonify({
            'error': 'Database service is temporarily unavailable.',
            'code': 'DATABASE_UNAVAILABLE'
        }), 503
    
    @app.errorhandler(DatabaseQueryError)
    def handle_query_error(error):
        """Handle database query errors."""
        logger.error(f"Database query error: {error}")
        return jsonify({
            'error': 'Failed to process your request.',
            'code': 'QUERY_ERROR'
        }), 500
    
    @app.errorhandler(DatabaseTransactionError)
    def handle_transaction_error(error):
        """Handle database transaction errors."""
        logger.error(f"Database transaction error: {error}")
        return jsonify({
            'error': 'Failed to save changes. Please try again.',
            'code': 'TRANSACTION_ERROR'
        }), 500
