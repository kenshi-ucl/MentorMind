from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Register auth routes
from app.routes.auth import auth_bp
api_bp.register_blueprint(auth_bp, url_prefix='/auth')

# Register chat routes
from app.routes.chat import chat_bp
api_bp.register_blueprint(chat_bp, url_prefix='/chat')


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'message': 'MentorMind API is running'}
