"""
Property-based tests for database progress tracking.

Feature: database-integration
Tests the SQLAlchemy-based ProgressService for quiz result persistence and progress calculation.
"""
import os
import uuid
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime

# Set test database before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.database import db
from app.services.progress_service import ProgressService
from app.models.user import User
from app.models.session import Session
from app.models.quiz_result import QuizResult


# Strategies for generating test data
user_id_strategy = st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
quiz_id_strategy = st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
topic_strategy = st.text(min_size=3, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')


def get_test_app():
    """Create a fresh test application with in-memory database."""
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


def create_test_user(app):
    """Create a test user and return the user object."""
    with app.app_context():
        user = User(
            id=str(uuid.uuid4()),
            name='Test User',
            is_anonymous=False
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@st.composite
def quiz_result_strategy(draw):
    """Generate valid quiz result data."""
    total = draw(st.integers(min_value=1, max_value=20))
    score = draw(st.integers(min_value=0, max_value=total))
    topic = draw(st.one_of(st.none(), topic_strategy))
    if topic:
        topic = topic.strip()
        if len(topic) < 3:
            topic = None
    return {
        'score': score,
        'total_questions': total,
        'topic': topic
    }


@st.composite
def multiple_quiz_results_strategy(draw):
    """Generate a list of quiz results for testing aggregation."""
    num_results = draw(st.integers(min_value=1, max_value=10))
    results = []
    for _ in range(num_results):
        result = draw(quiz_result_strategy())
        results.append(result)
    return results


class TestProgressCalculationAccuracy:
    """
    Property 7: Progress Calculation Accuracy
    
    For any user with N quiz results, the progress metrics (totalQuizzes, 
    totalQuestions, correctAnswers, successRate) SHALL be mathematically 
    consistent with the stored quiz results.
    
    **Validates: Requirements 5.1, 5.3, 5.5**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(results_data=multiple_quiz_results_strategy())
    def test_property_7_progress_calculation_accuracy(self, results_data):
        """
        Property 7: Progress Calculation Accuracy
        
        For any user with N quiz results, the progress metrics SHALL be 
        mathematically consistent with the stored quiz results.
        
        **Validates: Requirements 5.1, 5.3, 5.5**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            # Clean up any existing data
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            # Create a test user
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            progress_service = ProgressService()
            
            # Record all quiz results
            expected_total_quizzes = len(results_data)
            expected_total_questions = 0
            expected_correct_answers = 0
            
            for i, result_data in enumerate(results_data):
                quiz_id = f"quiz_{i}_{uuid.uuid4().hex[:8]}"
                progress_service.record_quiz_result(
                    user_id=user_id,
                    quiz_id=quiz_id,
                    topic=result_data['topic'],
                    score=result_data['score'],
                    total_questions=result_data['total_questions']
                )
                expected_total_questions += result_data['total_questions']
                expected_correct_answers += result_data['score']
            
            # Calculate expected success rate
            expected_success_rate = round(
                (expected_correct_answers / expected_total_questions * 100), 1
            ) if expected_total_questions > 0 else 0.0
            
            # Get progress and verify calculations
            progress = progress_service.get_progress(user_id)
            
            assert progress['totalQuizzes'] == expected_total_quizzes, \
                f"Expected {expected_total_quizzes} quizzes, got {progress['totalQuizzes']}"
            
            assert progress['totalQuestions'] == expected_total_questions, \
                f"Expected {expected_total_questions} questions, got {progress['totalQuestions']}"
            
            assert progress['correctAnswers'] == expected_correct_answers, \
                f"Expected {expected_correct_answers} correct, got {progress['correctAnswers']}"
            
            assert progress['successRate'] == expected_success_rate, \
                f"Expected {expected_success_rate}% success rate, got {progress['successRate']}%"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(True))
    def test_property_7_empty_progress_returns_zeros(self, _):
        """
        Property 7 (edge case): Empty progress returns zero values
        
        For a user with no quiz results, all progress metrics SHALL be zero.
        
        **Validates: Requirements 5.3, 5.5**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            # Create a test user with no quiz results
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            
            progress_service = ProgressService()
            progress = progress_service.get_progress(user.id)
            
            assert progress['totalQuizzes'] == 0
            assert progress['totalQuestions'] == 0
            assert progress['correctAnswers'] == 0
            assert progress['successRate'] == 0.0
            assert progress['topicProgress'] == {}
            assert progress['recentActivity'] == []
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        score=st.integers(min_value=0, max_value=100),
        total=st.integers(min_value=1, max_value=100)
    )
    def test_property_7_single_quiz_result_accuracy(self, score, total):
        """
        Property 7: Single quiz result accuracy
        
        For a single quiz result, progress metrics SHALL exactly match 
        the quiz result values.
        
        **Validates: Requirements 5.1, 5.3**
        """
        # Ensure score doesn't exceed total
        score = min(score, total)
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            
            progress_service = ProgressService()
            
            # Record a single quiz result
            progress_service.record_quiz_result(
                user_id=user.id,
                quiz_id=f"quiz_{uuid.uuid4().hex[:8]}",
                topic="Test Topic",
                score=score,
                total_questions=total
            )
            
            progress = progress_service.get_progress(user.id)
            
            assert progress['totalQuizzes'] == 1
            assert progress['totalQuestions'] == total
            assert progress['correctAnswers'] == score
            
            expected_rate = round((score / total * 100), 1)
            assert progress['successRate'] == expected_rate
            
            db.session.remove()
            db.drop_all()


class TestTopicProgressTracking:
    """
    Property 8: Topic Progress Tracking
    
    For any user with quiz results across multiple topics, the topic-wise 
    progress SHALL correctly aggregate scores per topic.
    
    **Validates: Requirements 5.4**
    """
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        topic1_results=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=10),
                st.integers(min_value=1, max_value=10)
            ),
            min_size=1,
            max_size=5
        ),
        topic2_results=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=10),
                st.integers(min_value=1, max_value=10)
            ),
            min_size=1,
            max_size=5
        )
    )
    def test_property_8_topic_progress_tracking(self, topic1_results, topic2_results):
        """
        Property 8: Topic Progress Tracking
        
        For any user with quiz results across multiple topics, the topic-wise 
        progress SHALL correctly aggregate scores per topic.
        
        **Validates: Requirements 5.4**
        """
        # Ensure scores don't exceed totals
        topic1_results = [(min(s, t), t) for s, t in topic1_results]
        topic2_results = [(min(s, t), t) for s, t in topic2_results]
        
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            
            progress_service = ProgressService()
            
            topic1 = "Mathematics"
            topic2 = "Science"
            
            # Record results for topic 1
            topic1_correct = 0
            topic1_total = 0
            for i, (score, total) in enumerate(topic1_results):
                progress_service.record_quiz_result(
                    user_id=user.id,
                    quiz_id=f"quiz_t1_{i}_{uuid.uuid4().hex[:8]}",
                    topic=topic1,
                    score=score,
                    total_questions=total
                )
                topic1_correct += score
                topic1_total += total
            
            # Record results for topic 2
            topic2_correct = 0
            topic2_total = 0
            for i, (score, total) in enumerate(topic2_results):
                progress_service.record_quiz_result(
                    user_id=user.id,
                    quiz_id=f"quiz_t2_{i}_{uuid.uuid4().hex[:8]}",
                    topic=topic2,
                    score=score,
                    total_questions=total
                )
                topic2_correct += score
                topic2_total += total
            
            # Get progress and verify topic-wise calculations
            progress = progress_service.get_progress(user.id)
            topic_progress = progress['topicProgress']
            
            # Verify topic 1 progress
            assert topic1 in topic_progress, f"Topic '{topic1}' should be in progress"
            expected_topic1_pct = round((topic1_correct / topic1_total * 100), 1)
            assert topic_progress[topic1]['percentage'] == expected_topic1_pct, \
                f"Topic 1 percentage: expected {expected_topic1_pct}, got {topic_progress[topic1]['percentage']}"
            assert topic_progress[topic1]['quizzes'] == len(topic1_results)
            assert topic_progress[topic1]['correct'] == topic1_correct
            assert topic_progress[topic1]['total'] == topic1_total
            
            # Verify topic 2 progress
            assert topic2 in topic_progress, f"Topic '{topic2}' should be in progress"
            expected_topic2_pct = round((topic2_correct / topic2_total * 100), 1)
            assert topic_progress[topic2]['percentage'] == expected_topic2_pct, \
                f"Topic 2 percentage: expected {expected_topic2_pct}, got {topic_progress[topic2]['percentage']}"
            assert topic_progress[topic2]['quizzes'] == len(topic2_results)
            assert topic_progress[topic2]['correct'] == topic2_correct
            assert topic_progress[topic2]['total'] == topic2_total
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        score=st.integers(min_value=8, max_value=10),
        total=st.integers(min_value=10, max_value=10)
    )
    def test_property_8_mastered_topic_detection(self, score, total):
        """
        Property 8: Mastered topic detection (>= 80%)
        
        For any topic with success rate >= 80%, it SHALL appear in 
        topics_mastered list.
        
        **Validates: Requirements 5.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            
            progress_service = ProgressService()
            topic = "Mastered Topic"
            
            progress_service.record_quiz_result(
                user_id=user.id,
                quiz_id=f"quiz_{uuid.uuid4().hex[:8]}",
                topic=topic,
                score=score,
                total_questions=total
            )
            
            mastered = progress_service.get_topics_mastered(user.id)
            percentage = (score / total) * 100
            
            if percentage >= 80.0:
                assert topic in mastered, \
                    f"Topic with {percentage}% should be mastered"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        score=st.integers(min_value=0, max_value=4),
        total=st.integers(min_value=10, max_value=10)
    )
    def test_property_8_needs_work_topic_detection(self, score, total):
        """
        Property 8: Needs work topic detection (< 50%)
        
        For any topic with success rate < 50%, it SHALL appear in 
        topics_needing_work list.
        
        **Validates: Requirements 5.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            
            progress_service = ProgressService()
            topic = "Needs Work Topic"
            
            progress_service.record_quiz_result(
                user_id=user.id,
                quiz_id=f"quiz_{uuid.uuid4().hex[:8]}",
                topic=topic,
                score=score,
                total_questions=total
            )
            
            needs_work = progress_service.get_topics_needing_work(user.id)
            percentage = (score / total) * 100
            
            if percentage < 50.0:
                assert topic in needs_work, \
                    f"Topic with {percentage}% should need work"
            
            db.session.remove()
            db.drop_all()
    
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(st.just(True))
    def test_property_8_null_topic_excluded_from_topic_progress(self, _):
        """
        Property 8: Null topics excluded from topic progress
        
        Quiz results with null topics SHALL NOT appear in topic progress.
        
        **Validates: Requirements 5.4**
        """
        app = get_test_app()
        with app.app_context():
            db.create_all()
            db.session.query(QuizResult).delete()
            db.session.query(Session).delete()
            db.session.query(User).delete()
            db.session.commit()
            
            user = User(
                id=str(uuid.uuid4()),
                name='Test User',
                is_anonymous=False
            )
            db.session.add(user)
            db.session.commit()
            
            progress_service = ProgressService()
            
            # Record a result with no topic
            progress_service.record_quiz_result(
                user_id=user.id,
                quiz_id=f"quiz_{uuid.uuid4().hex[:8]}",
                topic=None,
                score=5,
                total_questions=10
            )
            
            progress = progress_service.get_progress(user.id)
            
            # Overall progress should include the result
            assert progress['totalQuizzes'] == 1
            assert progress['totalQuestions'] == 10
            assert progress['correctAnswers'] == 5
            
            # But topic progress should be empty
            assert progress['topicProgress'] == {}
            
            db.session.remove()
            db.drop_all()
