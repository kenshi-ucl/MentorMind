"""Chat routes for TutorAgent interaction."""
import uuid
from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.services.agent_orchestrator import agent_orchestrator

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/message', methods=['POST'])
def send_message():
    """
    Process a chat message through the TutorAgent.
    
    Request body:
        - message: str (required) - The user's question or message
        - contentContext: list[str] (optional) - Context from uploaded content
        - stream: bool (optional) - Whether to stream the response (default: false)
    
    Returns:
        - 200: Response from TutorAgent with messageId
        - 400: Missing required fields or empty message
        - 503: TutorAgent unavailable
        
    For streaming responses (stream=true):
        Returns Server-Sent Events (SSE) stream with:
        - event: message - Contains response chunks
        - event: done - Signals completion with messageId
        - event: error - Contains error information
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    message = data.get('message')
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
    
    if stream:
        return _stream_response(message, content_context, message_id)
    else:
        return _non_stream_response(message, content_context, message_id)


def _non_stream_response(message: str, content_context: list, message_id: str):
    """Handle non-streaming chat response."""
    try:
        response = agent_orchestrator.process_chat(message, content_context, stream=False)
        
        if not response or response == "TutorAgent is not available.":
            return jsonify({'error': 'AI service temporarily unavailable'}), 503
        
        return jsonify({
            'response': response,
            'messageId': message_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500


def _stream_response(message: str, content_context: list, message_id: str):
    """Handle streaming chat response using Server-Sent Events (SSE)."""
    
    def generate():
        try:
            response_generator = agent_orchestrator.process_chat(
                message, 
                content_context, 
                stream=True
            )
            
            # Check if we got an error string instead of a generator
            if isinstance(response_generator, str):
                if response_generator == "TutorAgent is not available.":
                    yield f"event: error\ndata: {{\"error\": \"AI service temporarily unavailable\"}}\n\n"
                else:
                    # Single response, send as one chunk
                    yield f"event: message\ndata: {_escape_sse_data(response_generator)}\n\n"
                yield f"event: done\ndata: {{\"messageId\": \"{message_id}\"}}\n\n"
                return
            
            # Stream the response chunks
            full_response = ""
            for chunk in response_generator:
                if chunk:
                    full_response += chunk
                    yield f"event: message\ndata: {_escape_sse_data(chunk)}\n\n"
            
            # Send completion event
            yield f"event: done\ndata: {{\"messageId\": \"{message_id}\"}}\n\n"
            
        except Exception as e:
            error_msg = str(e)
            yield f"event: error\ndata: {{\"error\": \"{_escape_sse_data(error_msg)}\"}}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


def _escape_sse_data(data: str) -> str:
    """Escape data for SSE format (handle newlines and special characters)."""
    # Replace newlines with escaped version for JSON
    # SSE data field should not contain raw newlines
    return data.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
