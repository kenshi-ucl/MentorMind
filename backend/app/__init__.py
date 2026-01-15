import os
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# SocketIO instance - accessible for running with eventlet
socketio = None


def create_app():
    """Create and configure the Flask application."""
    global socketio
    
    app = Flask(__name__)
    
    # Enable CORS for frontend communication
    CORS(app, origins=["http://localhost:5173", "http://localhost:5174"])
    
    # Initialize database
    from app.database import init_db
    init_db(app)
    
    # Register error handlers for database operations
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize SocketIO
    from app.sockets import init_socketio
    socketio = init_socketio(app)
    
    return app
