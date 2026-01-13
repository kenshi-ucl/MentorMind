"""Property-based tests for quiz functionality.

Feature: mentormind-ai-tutor
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from app.services.quiz_service import QuizService
from app.models.quiz import Quiz, QuizQuestion, QuizResult


# Strategies for quiz testing
topic_strategy = st.text(min_size=3, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')
user_id_strategy = st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')
question_count_strategy = st.integers(min_value=1, max_value=10)


# Strategy for generating valid quiz questions
@st.composite
def quiz_question_strategy(draw):
    """Generate a valid QuizQuestion."""
    question_text = draw(st.text(min_size=5, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ?'))
    num_options = draw(st.integers(min_value=2, max_value=5))
    options = [draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')) for _ in range(num_options)]
    correct_index = draw(st.integers(min_value=0, max_value=num_options - 1))
    explanation = draw(st.text(min_size=5, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .'))
    
    return QuizQuestion(
        id=draw(st.text(min_size=3, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz0123456789')),
        question=question_text,
        options=options,
        correct_index=correct_index,
        explanation=explanation
    )


# Strategy for generating a list of quiz questions
@st.composite
def quiz_questions_list_strategy(draw, min_questions=1, max_questions=10):
    """Generate a list of valid QuizQuestions."""
    num_questions = draw(st.integers(min_value=min_questions, max_value=max_questions))
    questions = []
    for i in range(num_questions):
        q = draw(quiz_question_strategy())
        # Ensure unique IDs
        q.id = f"q{i+1}"
        questions.append(q)
    return questions


class TestQuizGenerationProperties:
    """Property-based tests for quiz generation."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        user_id=user_id_strategy,
        topic=topic_strategy,
        question_count=question_count_strategy
    )
    def test_property_10_quiz_generation_structure_validity(self, user_id, topic, question_count):
        """
        Property 10: Quiz Generation Structure Validity
        
        For any valid topic string or content ID, the QuizAgent should generate 
        a quiz where each question has: a non-empty question string, at least 2 
        options, a valid correctIndex within the options range, and a non-empty 
        explanation.
        
        Validates: Requirements 6.1
        """
        # Create fresh quiz service for each test
        quiz_service = QuizService()
        
        # Ensure topic is not empty after stripping
        topic = topic.strip()
        assume(len(topic) >= 3)
        
        # Generate quiz
        quiz, error = quiz_service.generate_quiz(
            user_id=user_id,
            topic=topic,
            question_count=question_count
        )
        
        # Quiz generation should succeed
        assert error is None, f"Quiz generation failed: {error}"
        assert quiz is not None
        
        # Verify quiz structure
        assert quiz.id is not None and len(quiz.id) > 0
        assert quiz.user_id == user_id
        assert quiz.topic == topic
        assert len(quiz.questions) > 0
        
        # Verify each question structure
        for question in quiz.questions:
            # Non-empty question string
            assert question.question is not None
            assert len(question.question) > 0, "Question text must not be empty"
            
            # At least 2 options
            assert len(question.options) >= 2, f"Question must have at least 2 options, got {len(question.options)}"
            
            # Valid correctIndex within options range
            assert 0 <= question.correct_index < len(question.options), \
                f"correctIndex {question.correct_index} out of range for {len(question.options)} options"
            
            # Non-empty explanation
            assert question.explanation is not None
            assert len(question.explanation) > 0, "Explanation must not be empty"
            
            # Question should pass its own validation
            assert question.is_valid(), "Question failed internal validation"


class TestQuizAnswerRecordingProperties:
    """Property-based tests for quiz answer recording."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        user_id=user_id_strategy,
        questions=quiz_questions_list_strategy(min_questions=2, max_questions=5)
    )
    def test_property_11_quiz_answer_recording(self, user_id, questions):
        """
        Property 11: Quiz Answer Recording
        
        For any quiz question and selected answer index, the system should 
        record the answer and the recorded answer should match the submitted 
        value when retrieved.
        
        Validates: Requirements 6.3
        """
        quiz_service = QuizService()
        
        # Create a quiz directly with the generated questions
        quiz = Quiz.create(
            user_id=user_id,
            questions=questions,
            topic="Test Topic"
        )
        
        # Store the quiz in the service
        quiz_service._quizzes[quiz.id] = quiz
        
        # Generate random valid answers for each question
        answers = []
        for question in questions:
            # Pick a random valid answer index
            answer_idx = question.correct_index  # Use correct answer for simplicity
            answers.append(answer_idx)
        
        # Submit the quiz
        result, error = quiz_service.submit_quiz(
            quiz_id=quiz.id,
            user_id=user_id,
            answers=answers
        )
        
        # Submission should succeed
        assert error is None, f"Quiz submission failed: {error}"
        assert result is not None
        
        # Verify each recorded answer matches submitted value
        for i, submitted_answer in enumerate(answers):
            recorded_answer = quiz_service.get_answer(quiz.id, user_id, i)
            assert recorded_answer is not None, f"Answer for question {i} not recorded"
            assert recorded_answer == submitted_answer, \
                f"Recorded answer {recorded_answer} doesn't match submitted {submitted_answer} for question {i}"


class TestQuizScoreCalculationProperties:
    """Property-based tests for quiz score calculation."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        questions=quiz_questions_list_strategy(min_questions=1, max_questions=10),
        answer_correctness=st.lists(st.booleans(), min_size=1, max_size=10)
    )
    def test_property_12_quiz_score_calculation_correctness(self, questions, answer_correctness):
        """
        Property 12: Quiz Score Calculation Correctness
        
        For any completed quiz with N questions and a set of answers, the 
        calculated score should equal the count of answers where the selected 
        index matches the correct index, divided by N.
        
        Validates: Requirements 6.4, 6.5
        """
        quiz_service = QuizService()
        
        # Ensure we have matching lengths
        num_questions = len(questions)
        answer_correctness = answer_correctness[:num_questions]
        while len(answer_correctness) < num_questions:
            answer_correctness.append(False)
        
        # Generate answers based on correctness flags
        answers = []
        expected_correct = 0
        
        for i, (question, should_be_correct) in enumerate(zip(questions, answer_correctness)):
            if should_be_correct:
                # Use the correct answer
                answers.append(question.correct_index)
                expected_correct += 1
            else:
                # Use an incorrect answer (pick a different index)
                wrong_index = (question.correct_index + 1) % len(question.options)
                answers.append(wrong_index)
        
        # Calculate score using the service method
        correct_count, total, score = quiz_service.calculate_score(answers, questions)
        
        # Verify score calculation
        assert total == num_questions, f"Total should be {num_questions}, got {total}"
        assert correct_count == expected_correct, \
            f"Correct count should be {expected_correct}, got {correct_count}"
        
        # Verify score percentage
        expected_score = expected_correct / num_questions if num_questions > 0 else 0.0
        assert abs(score - expected_score) < 0.0001, \
            f"Score should be {expected_score}, got {score}"
        
        # Also test through QuizResult.create
        result = QuizResult.create(
            quiz_id="test_quiz",
            user_id="test_user",
            answers=answers,
            questions=questions
        )
        
        assert result.correct_count == expected_correct
        assert result.total_questions == num_questions
        assert abs(result.score - expected_score) < 0.0001
