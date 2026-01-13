"""Property-based tests for progress tracking functionality.

Feature: mentormind-ai-tutor
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from app.services.progress_service import ProgressService, progress_service
from app.services.quiz_service import QuizService, quiz_service
from app.models.progress import UserProgress, TopicProgress, ProgressEntry
from app.models.quiz import Quiz, QuizQuestion, QuizResult


# Strategies for progress testing
user_id_strategy = st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
topic_strategy = st.text(min_size=3, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')


@st.composite
def quiz_question_strategy(draw):
    """Generate a valid QuizQuestion."""
    question_text = draw(st.text(min_size=5, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ?'))
    num_options = draw(st.integers(min_value=2, max_value=4))
    options = [draw(st.text(min_size=1, max_size=30, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')) for _ in range(num_options)]
    correct_index = draw(st.integers(min_value=0, max_value=num_options - 1))
    explanation = draw(st.text(min_size=5, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .'))
    
    return QuizQuestion(
        id=draw(st.text(min_size=3, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')),
        question=question_text,
        options=options,
        correct_index=correct_index,
        explanation=explanation
    )


@st.composite
def quiz_result_data_strategy(draw):
    """Generate quiz result data with correct and total counts."""
    total = draw(st.integers(min_value=1, max_value=20))
    correct = draw(st.integers(min_value=0, max_value=total))
    return correct, total


class TestProgressSuccessRateProperties:
    """Property-based tests for success rate calculation."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        correct=st.integers(min_value=0, max_value=1000),
        total=st.integers(min_value=1, max_value=1000)
    )
    def test_property_13_progress_success_rate_calculation(self, correct, total):
        """
        Property 13: Progress Success Rate Calculation
        
        For any set of quiz results for a user, the success rate displayed 
        should equal (total correct answers / total questions attempted) * 100, 
        rounded appropriately.
        
        Validates: Requirements 7.2
        """
        # Ensure correct doesn't exceed total
        correct = min(correct, total)
        
        progress_svc = ProgressService()
        
        # Calculate success rate using the service method
        calculated_rate = progress_svc.calculate_success_rate(correct, total)
        
        # Calculate expected rate
        expected_rate = round((correct / total) * 100, 1)
        
        # Verify the calculation matches
        assert calculated_rate == expected_rate, \
            f"Success rate should be {expected_rate}, got {calculated_rate}"
        
        # Verify rate is within valid range
        assert 0.0 <= calculated_rate <= 100.0, \
            f"Success rate {calculated_rate} should be between 0 and 100"
        
        # Test through UserProgress model
        progress = UserProgress(
            user_id="test_user",
            total_questions=total,
            correct_answers=correct
        )
        
        assert progress.success_rate == expected_rate, \
            f"UserProgress.success_rate should be {expected_rate}, got {progress.success_rate}"
    
    @settings(max_examples=100, deadline=None)
    @given(total=st.integers(min_value=0, max_value=0))
    def test_property_13_zero_questions_returns_zero_rate(self, total):
        """
        Edge case: When no questions have been attempted, success rate should be 0.
        
        Validates: Requirements 7.2
        """
        progress_svc = ProgressService()
        
        calculated_rate = progress_svc.calculate_success_rate(0, 0)
        assert calculated_rate == 0.0, "Success rate with 0 questions should be 0.0"
        
        progress = UserProgress(user_id="test_user", total_questions=0, correct_answers=0)
        assert progress.success_rate == 0.0


class TestTopicMasteryCategorizationProperties:
    """Property-based tests for topic mastery categorization."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        topic=topic_strategy,
        correct=st.integers(min_value=0, max_value=100),
        total=st.integers(min_value=1, max_value=100)
    )
    def test_property_14_topic_mastery_categorization(self, topic, correct, total):
        """
        Property 14: Topic Mastery Categorization
        
        For any topic with quiz attempts, if the success rate for that topic 
        is >= 80%, it should appear in "topics mastered"; if < 50%, it should 
        appear in "topics needing improvement".
        
        Validates: Requirements 7.3
        """
        topic = topic.strip()
        assume(len(topic) >= 3)
        
        # Ensure correct doesn't exceed total
        correct = min(correct, total)
        
        # Create topic progress
        topic_progress = TopicProgress(
            topic=topic,
            attempts=1,
            correct=correct,
            total_questions=total
        )
        
        success_rate = topic_progress.success_rate
        
        # Create user progress with this topic
        progress = UserProgress(
            user_id="test_user",
            topics_attempted={topic: topic_progress}
        )
        
        # Test categorization
        if success_rate >= 80.0:
            assert topic in progress.topics_mastered, \
                f"Topic '{topic}' with {success_rate}% should be in topics_mastered"
            assert topic not in progress.topics_needing_work, \
                f"Topic '{topic}' with {success_rate}% should not be in topics_needing_work"
        elif success_rate < 50.0:
            assert topic in progress.topics_needing_work, \
                f"Topic '{topic}' with {success_rate}% should be in topics_needing_work"
            assert topic not in progress.topics_mastered, \
                f"Topic '{topic}' with {success_rate}% should not be in topics_mastered"
        else:
            # Between 50% and 80% - should be in neither list
            assert topic not in progress.topics_mastered, \
                f"Topic '{topic}' with {success_rate}% should not be in topics_mastered"
            assert topic not in progress.topics_needing_work, \
                f"Topic '{topic}' with {success_rate}% should not be in topics_needing_work"
    
    @settings(max_examples=100, deadline=None)
    @given(success_rate=st.floats(min_value=0.0, max_value=100.0, allow_nan=False))
    def test_property_14_categorize_topic_mastery_function(self, success_rate):
        """
        Test the categorize_topic_mastery helper function.
        
        Validates: Requirements 7.3
        """
        progress_svc = ProgressService()
        
        category = progress_svc.categorize_topic_mastery(success_rate)
        
        if success_rate >= 80.0:
            assert category == "mastered", \
                f"Rate {success_rate}% should be 'mastered', got '{category}'"
        elif success_rate < 50.0:
            assert category == "needs_work", \
                f"Rate {success_rate}% should be 'needs_work', got '{category}'"
        else:
            assert category == "in_progress", \
                f"Rate {success_rate}% should be 'in_progress', got '{category}'"


class TestProgressUpdateAfterQuizProperties:
    """Property-based tests for progress updates after quiz completion."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        user_id=user_id_strategy,
        topic=topic_strategy,
        num_questions=st.integers(min_value=1, max_value=5)
    )
    def test_property_15_progress_update_after_quiz(self, user_id, topic, num_questions):
        """
        Property 15: Progress Update After Quiz
        
        For any newly completed quiz, the progress data should be updated to 
        include the new quiz results, and the total quizzes count should 
        increment by 1.
        
        Validates: Requirements 7.5
        """
        topic = topic.strip()
        assume(len(topic) >= 3)
        
        # Create fresh services for isolation
        test_quiz_service = QuizService()
        
        # Create questions for the quiz
        questions = []
        for i in range(num_questions):
            questions.append(QuizQuestion(
                id=f"q{i+1}",
                question=f"Test question {i+1}?",
                options=["Option A", "Option B", "Option C"],
                correct_index=0,
                explanation=f"Explanation for question {i+1}"
            ))
        
        # Create and store a quiz
        quiz = Quiz.create(
            user_id=user_id,
            questions=questions,
            topic=topic
        )
        test_quiz_service._quizzes[quiz.id] = quiz
        
        # Get initial progress (should be empty)
        initial_results = test_quiz_service.get_user_results(user_id)
        initial_quiz_count = len(initial_results)
        
        # Submit the quiz with all correct answers
        answers = [q.correct_index for q in questions]
        result, error = test_quiz_service.submit_quiz(
            quiz_id=quiz.id,
            user_id=user_id,
            answers=answers
        )
        
        assert error is None, f"Quiz submission failed: {error}"
        assert result is not None
        
        # Get updated results
        updated_results = test_quiz_service.get_user_results(user_id)
        updated_quiz_count = len(updated_results)
        
        # Verify quiz count incremented by 1
        assert updated_quiz_count == initial_quiz_count + 1, \
            f"Quiz count should increment from {initial_quiz_count} to {initial_quiz_count + 1}, got {updated_quiz_count}"
        
        # Verify the new result is included
        result_ids = [r.id for r in updated_results]
        assert result.id in result_ids, "New quiz result should be in user's results"
        
        # Verify result data is correct
        assert result.quiz_id == quiz.id
        assert result.user_id == user_id
        assert result.total_questions == num_questions
        assert result.correct_count == num_questions  # All answers were correct
        assert result.score == 1.0  # 100% score
