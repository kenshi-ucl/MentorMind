from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Register auth routes
from app.routes.auth import auth_bp
api_bp.register_blueprint(auth_bp, url_prefix='/auth')

# Register chat routes
from app.routes.chat import chat_bp
api_bp.register_blueprint(chat_bp, url_prefix='/chat')

# Register content routes
from app.routes.content import content_bp
api_bp.register_blueprint(content_bp, url_prefix='/content')

# Register quiz routes
from app.routes.quiz import quiz_bp
api_bp.register_blueprint(quiz_bp, url_prefix='/quiz')

# Register progress routes
from app.routes.progress import progress_bp
api_bp.register_blueprint(progress_bp, url_prefix='/progress')

# Register seed routes for demo data
from app.routes.seed import seed_bp
api_bp.register_blueprint(seed_bp)


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'message': 'MentorMind API is running'}
