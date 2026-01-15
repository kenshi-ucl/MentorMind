"""Chat routes for TutorAgent interaction with conversation history."""
import uuid
from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.services.agent_orchestrator import agent_orchestrator
from app.services.auth_service import auth_service
from app.database import db
from app.models.conversation import Conversation, Message
from app.routes.auth import require_auth

chat_bp = Blueprint('chat', __name__)


def get_current_user():
    """Get the current user from the authorization header."""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    return auth_service.get_user_by_session(token)


@chat_bp.route('/conversations', methods=['GET'])
@require_auth
def get_conversations():
    """
    Get all conversations for the current user.
    
    Returns:
        - 200: List of conversations
    """
    user = request.current_user
    
    conversations = Conversation.query.filter_by(
        user_id=user.id,
        is_active=True
    ).order_by(Conversation.updated_at.desc()).all()
    
    return jsonify({
        'conversations': [conv.to_dict() for conv in conversations]
    }), 200


@chat_bp.route('/conversations', methods=['POST'])
@require_auth
def create_conversation():
    """
    Create a new conversation.
    
    Returns:
        - 201: New conversation created
    """
    user = request.current_user
    
    conversation = Conversation(
        user_id=user.id,
        title='New Conversation'
    )
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify(conversation.to_dict()), 201


@chat_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """
    Get a specific conversation with all messages.
    
    Returns:
        - 200: Conversation with messages
        - 404: Conversation not found
    """
    user = request.current_user
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=user.id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify(conversation.to_dict(include_messages=True)), 200


@chat_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    """
    Delete (soft delete) a conversation.
    
    Returns:
        - 200: Conversation deleted
        - 404: Conversation not found
    """
    user = request.current_user
    
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=user.id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    conversation.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Conversation deleted'}), 200


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """
    Process a chat message through the TutorAgent.
    
    Request body:
        - message: str (required) - The user's question or message
        - conversationId: int (optional) - Conversation ID to add message to
        - contentContext: list[str] (optional) - Context from uploaded content
        - stream: bool (optional) - Whether to stream the response (default: false)
    
    Returns:
        - 200: Response from TutorAgent with messageId and conversationId
        - 400: Missing required fields or empty message
        - 503: TutorAgent unavailable
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    message = data.get('message')
    conversation_id = data.get('conversationId')
    content_context = data.get('contentContext', [])
    stream = data.get('stream', False)
    
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
    
    # Generate message ID upfront
    message_id = str(uuid.uuid4())
    
    # Get user and conversation
    user = get_current_user()
    conv_id = None
    conversation_history = []
    
    if user:
        conversation = None
        if conversation_id:
            conversation = Conversation.query.filter_by(
                id=conversation_id,
                user_id=user.id
            ).first()
        
        # Create new conversation if needed
        if not conversation:
            conversation = Conversation(
                user_id=user.id,
                title=message[:50] + ('...' if len(message) > 50 else '')
            )
            db.session.add(conversation)
            db.session.commit()
        
        # Extract conversation ID (avoid SQLAlchemy detached instance issues)
        conv_id = conversation.id
        
        # Get conversation history for AI context
        conversation_history = conversation.get_context_messages(limit=20)
        
        # Save user message to database
        user_msg = Message(
            conversation_id=conv_id,
            role='user',
            content=message,
            message_id=message_id
        )
        db.session.add(user_msg)
        db.session.commit()
    
    if stream:
        return _stream_response(message, content_context, message_id, 
                               conv_id, conversation_history)
    else:
        return _non_stream_response(message, content_context, message_id,
                                   conv_id, conversation_history)


def _non_stream_response(message: str, content_context: list, message_id: str,
                        conv_id: int, conversation_history: list):
    """Handle non-streaming chat response."""
    try:
        response = agent_orchestrator.process_chat(
            message, 
            content_context, 
            stream=False,
            conversation_history=conversation_history
        )
        
        if not response or response == "TutorAgent is not available.":
            return jsonify({'error': 'AI service temporarily unavailable'}), 503
        
        # Save assistant response to database
        if conv_id:
            assistant_msg = Message(
                conversation_id=conv_id,
                role='assistant',
                content=response,
                message_id=str(uuid.uuid4())
            )
            db.session.add(assistant_msg)
            
            # Update conversation timestamp
            conversation = Conversation.query.get(conv_id)
            if conversation:
                conversation.updated_at = db.func.now()
            db.session.commit()
        
        return jsonify({
            'response': response,
            'messageId': message_id,
            'conversationId': conv_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500


def _stream_response(message: str, content_context: list, message_id: str,
                    conv_id: int, conversation_history: list):
    """Handle streaming chat response using Server-Sent Events (SSE)."""
    
    def generate():
        full_response = ""
        try:
            response_generator = agent_orchestrator.process_chat(
                message, 
                content_context, 
                stream=True,
                conversation_history=conversation_history
            )
            
            # Check if we got an error string instead of a generator
            if isinstance(response_generator, str):
                if response_generator == "TutorAgent is not available.":
                    yield f"event: error\ndata: {{\"error\": \"AI service temporarily unavailable\"}}\n\n"
                else:
                    # Single response, send as one chunk
                    full_response = response_generator
                    yield f"event: message\ndata: {_escape_sse_data(response_generator)}\n\n"
                
                # Save to database
                if conv_id and full_response:
                    _save_assistant_message(conv_id, full_response)
                
                yield f"event: done\ndata: {{\"messageId\": \"{message_id}\", \"conversationId\": {conv_id or 'null'}}}\n\n"
                return
            
            # Stream the response chunks
            for chunk in response_generator:
                if chunk:
                    full_response += chunk
                    yield f"event: message\ndata: {_escape_sse_data(chunk)}\n\n"
            
            # Save complete response to database
            if conv_id and full_response:
                _save_assistant_message(conv_id, full_response)
            
            # Send completion event
            yield f"event: done\ndata: {{\"messageId\": \"{message_id}\", \"conversationId\": {conv_id or 'null'}}}\n\n"
            
        except Exception as e:
            error_msg = str(e)
            yield f"event: error\ndata: {{\"error\": \"{_escape_sse_data(error_msg)}\"}}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


def _save_assistant_message(conv_id: int, content: str):
    """Save assistant message to database."""
    assistant_msg = Message(
        conversation_id=conv_id,
        role='assistant',
        content=content,
        message_id=str(uuid.uuid4())
    )
    db.session.add(assistant_msg)
    
    # Update conversation timestamp
    conversation = Conversation.query.get(conv_id)
    if conversation:
        conversation.updated_at = db.func.now()
    
    db.session.commit()


def _escape_sse_data(data: str) -> str:
    """Escape data for SSE format (handle newlines and special characters)."""
    return data.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
