"""Progress routes for user learning progress tracking."""
from flask import Blueprint, request, jsonify
from app.services.progress_service import progress_service
from app.routes.auth import require_auth
from app.errors import db_error_handler

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('', methods=['GET'])
@require_auth
@db_error_handler
def get_progress():
    """
    Get user progress data.
    
    Returns progress metrics including:
    - Total quizzes taken
    - Overall success rate
    - Topics mastered (>= 80% success rate)
    - Topics needing improvement (< 50% success rate)
    - Progress over time
    
    Returns:
        - 200: Progress data
        - 401: Unauthorized
    """
    user_id = request.current_user.id
    
    # Use the new database-backed get_progress method
    progress = progress_service.get_progress(user_id)
    
    # Categorize topics for frontend display
    topics_mastered = []
    topics_needing_work = []
    topics_in_progress = []
    
    for topic, data in progress.get('topicProgress', {}).items():
        percentage = data.get('percentage', 0)
        if percentage >= 80.0:
            topics_mastered.append(topic)
        elif percentage < 50.0:
            topics_needing_work.append(topic)
        else:
            topics_in_progress.append(topic)
    
    return jsonify({
        'progressData': {
            'totalQuizzes': progress.get('totalQuizzes', 0),
            'totalQuestions': progress.get('totalQuestions', 0),
            'correctAnswers': progress.get('correctAnswers', 0),
            'successRate': progress.get('successRate', 0.0),
            'topicProgress': progress.get('topicProgress', {}),
            'recentActivity': progress.get('recentActivity', []),
            'topicsMastered': topics_mastered,
            'topicsNeedingWork': topics_needing_work,
            'topicsInProgress': topics_in_progress
        }
    }), 200


@progress_bp.route('/results', methods=['GET'])
@require_auth
@db_error_handler
def get_quiz_results():
    """
    Get all quiz results for the current user.
    
    Returns:
        - 200: List of quiz results
        - 401: Unauthorized
    """
    user_id = request.current_user.id
    
    results = progress_service.get_quiz_results(user_id)
    
    return jsonify({
        'results': [{
            'id': r.id,
            'quizId': r.quiz_id,
            'topic': r.topic,
            'score': r.score,
            'totalQuestions': r.total_questions,
            'percentage': r.percentage,
            'createdAt': r.created_at.isoformat() if r.created_at else None
        } for r in results]
    }), 200


@progress_bp.route('/topics/mastered', methods=['GET'])
@require_auth
@db_error_handler
def get_topics_mastered():
    """
    Get list of topics the user has mastered (>= 80% success rate).
    
    Returns:
        - 200: List of mastered topics
        - 401: Unauthorized
    """
    user_id = request.current_user.id
    
    topics = progress_service.get_topics_mastered(user_id)
    
    return jsonify({
        'topics': topics
    }), 200


@progress_bp.route('/topics/needs-work', methods=['GET'])
@require_auth
@db_error_handler
def get_topics_needing_work():
    """
    Get list of topics needing improvement (< 50% success rate).
    
    Returns:
        - 200: List of topics needing work
        - 401: Unauthorized
    """
    user_id = request.current_user.id
    
    topics = progress_service.get_topics_needing_work(user_id)
    
    return jsonify({
        'topics': topics
    }), 200
