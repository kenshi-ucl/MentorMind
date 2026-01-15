"""Entry point for running the Flask development server with SocketIO."""
import eventlet
eventlet.monkey_patch()

from app import create_app

app = create_app()

# Import socketio after create_app() has initialized it
from app import socketio

if __name__ == '__main__':
    # Use socketio.run() with use_reloader=False to avoid eventlet issues
    socketio.run(app, debug=True, port=5000, host='127.0.0.1', use_reloader=False)
