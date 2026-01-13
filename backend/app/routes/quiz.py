"""Quiz routes for quiz generation and submission."""
from flask import Blueprint, request, jsonify
from app.services.quiz_service import quiz_service
from app.services.auth_service import auth_service

quiz_bp = Blueprint('quiz', __name__)


def get_current_user_id() -> tuple[str | None, dict | None, int | None]:
    """
    Get the current user ID from the authorization header.
    
    Returns:
        Tuple of (user_id, error_response, status_code).
        If successful, error_response and status_code are None.
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None, {'error': 'Authorization header required'}, 401
    
    # Handle both "Bearer <token>" and just "<token>" formats
    token = auth_header
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    # Validate token and get user
    user = auth_service.validate_token(token)
    if not user:
        return None, {'error': 'Invalid or expired token'}, 401
    
    return user.id, None, None


@quiz_bp.route('/generate', methods=['POST'])
def generate_quiz():
    """
    Generate a quiz from a topic or content.
    
    Request body:
        - topic: str (optional) - Topic for the quiz
        - contentId: str (optional) - Content ID to base questions on
        - questionCount: int (optional, default 5) - Number of questions
    
    At least one of topic or contentId must be provided.
    
    Returns:
        - 200: Generated quiz with questions
        - 400: Invalid request (missing topic/contentId, invalid count)
        - 401: Unauthorized
        - 404: Content not found
        - 500: Quiz generation failed
    """
    user_id, error, status = get_current_user_id()
    if error:
        return jsonify(error), status
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    topic = data.get('topic')
    content_id = data.get('contentId')
    question_count = data.get('questionCount', 5)
    
    # Validate question count
    if not isinstance(question_count, int):
        return jsonify({'error': 'questionCount must be an integer'}), 400
    
    # Generate quiz
    quiz, error_msg = quiz_service.generate_quiz(
        user_id=user_id,
        topic=topic,
        content_id=content_id,
        question_count=question_count
    )
    
    if error_msg:
        # Determine appropriate status code
        if "not found" in error_msg.lower():
            return jsonify({'error': error_msg}), 404
        elif "not authorized" in error_msg.lower():
            return jsonify({'error': error_msg}), 403
        else:
            return jsonify({'error': error_msg}), 400
    
    # Return quiz without correct answers for client
    quiz_dict = quiz.to_dict()
    
    # Remove correct answers from response (client shouldn't see them)
    for question in quiz_dict['questions']:
        del question['correctIndex']
        del question['explanation']
    
    return jsonify({
        'quizId': quiz.id,
        'questions': quiz_dict['questions']
    }), 200


@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    """
    Submit quiz answers and get results.
    
    Request body:
        - quizId: str (required) - ID of the quiz
        - answers: list[int] (required) - List of answer indices
    
    Returns:
        - 200: Quiz results with score and explanations
        - 400: Invalid request (missing fields, wrong answer count)
        - 401: Unauthorized
        - 404: Quiz not found
        - 409: Quiz already submitted
    """
    user_id, error, status = get_current_user_id()
    if error:
        return jsonify(error), status
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body is required'}), 400
    
    quiz_id = data.get('quizId')
    answers = data.get('answers')
    
    # Validate required fields
    if not quiz_id:
        return jsonify({'error': 'quizId is required'}), 400
    
    if answers is None:
        return jsonify({'error': 'answers is required'}), 400
    
    if not isinstance(answers, list):
        return jsonify({'error': 'answers must be a list'}), 400
    
    # Validate all answers are integers
    for i, answer in enumerate(answers):
        if not isinstance(answer, int):
            return jsonify({'error': f'Answer at index {i} must be an integer'}), 400
    
    # Submit quiz
    result, error_msg = quiz_service.submit_quiz(
        quiz_id=quiz_id,
        user_id=user_id,
        answers=answers
    )
    
    if error_msg:
        # Determine appropriate status code
        if "not found" in error_msg.lower():
            return jsonify({'error': error_msg}), 404
        elif "not authorized" in error_msg.lower():
            return jsonify({'error': error_msg}), 403
        elif "already been submitted" in error_msg.lower():
            return jsonify({'error': error_msg}), 409
        else:
            return jsonify({'error': error_msg}), 400
    
    # Get the quiz to include question details in response
    quiz = quiz_service.get_quiz(quiz_id)
    
    # Build detailed results with explanations for incorrect answers
    results = []
    for i, question in enumerate(quiz.questions):
        user_answer = answers[i] if i < len(answers) else -1
        is_correct = user_answer == question.correct_index
        
        result_item = {
            'questionId': question.id,
            'question': question.question,
            'userAnswer': user_answer,
            'correctAnswer': question.correct_index,
            'isCorrect': is_correct,
            'options': question.options
        }
        
        # Include explanation for incorrect answers
        if not is_correct:
            result_item['explanation'] = question.explanation
        
        results.append(result_item)
    
    return jsonify({
        'score': result.score,
        'correctCount': result.correct_count,
        'totalQuestions': result.total_questions,
        'results': results
    }), 200


@quiz_bp.route('/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id: str):
    """
    Get a quiz by ID.
    
    Returns:
        - 200: Quiz data
        - 401: Unauthorized
        - 404: Quiz not found
    """
    user_id, error, status = get_current_user_id()
    if error:
        return jsonify(error), status
    
    quiz = quiz_service.get_quiz(quiz_id)
    
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    if quiz.user_id != user_id:
        return jsonify({'error': 'Not authorized to access this quiz'}), 403
    
    # Return quiz without correct answers
    quiz_dict = quiz.to_dict()
    for question in quiz_dict['questions']:
        del question['correctIndex']
        del question['explanation']
    
    return jsonify(quiz_dict), 200


@quiz_bp.route('/list', methods=['GET'])
def list_quizzes():
    """
    List all quizzes for the current user.
    
    Returns:
        - 200: List of quizzes
        - 401: Unauthorized
    """
    user_id, error, status = get_current_user_id()
    if error:
        return jsonify(error), status
    
    quizzes = quiz_service.get_user_quizzes(user_id)
    
    # Return quizzes without correct answers
    quiz_list = []
    for quiz in quizzes:
        quiz_dict = quiz.to_dict()
        for question in quiz_dict['questions']:
            del question['correctIndex']
            del question['explanation']
        quiz_list.append(quiz_dict)
    
    return jsonify({'quizzes': quiz_list}), 200


@quiz_bp.route('/results', methods=['GET'])
def list_results():
    """
    List all quiz results for the current user.
    
    Returns:
        - 200: List of quiz results
        - 401: Unauthorized
    """
    user_id, error, status = get_current_user_id()
    if error:
        return jsonify(error), status
    
    results = quiz_service.get_user_results(user_id)
    
    return jsonify({
        'results': [r.to_dict() for r in results]
    }), 200
