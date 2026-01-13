from flask import Flask
from flask_cors import CORS

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for frontend communication
    CORS(app, origins=["http://localhost:5173", "http://localhost:5174"])
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
