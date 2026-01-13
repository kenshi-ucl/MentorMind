"""Chat routes for TutorAgent interaction."""
from flask import Blueprint, request, jsonify
from app.services.agent_orchestrator import agent_orchestrator

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """
    Process a chat message through the TutorAgent.
    
    Request body:
        - message: str (required) - The user's question or message
        - contentContext: list[str] (optional) - Context from uploaded content
    
    Returns:
        - 200: Response from TutorAgent with messageId
        - 400: Missing required fields or empty message
        - 503: TutorAgent unavailable
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    message = data.get('message')
    content_context = data.get('contentContext', [])
    
    # Validate message
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    if not isinstance(message, str):
        return jsonify({'error': 'Message must be a string'}), 400
    
    message = message.strip()
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Validate content context if provided
    if content_context and not isinstance(content_context, list):
        return jsonify({'error': 'contentContext must be a list'}), 400
    
    # Process through TutorAgent
    try:
        response = agent_orchestrator.process_chat(message, content_context)
        
        if not response or response == "TutorAgent is not available.":
            return jsonify({'error': 'AI service temporarily unavailable'}), 503
        
        # Generate a simple message ID
        import uuid
        message_id = str(uuid.uuid4())
        
        return jsonify({
            'response': response,
            'messageId': message_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500
