"""Quiz service for quiz generation and management."""
from typing import Optional
import uuid
from app.models.quiz import Quiz, QuizQuestion, QuizResult
from app.services.agent_orchestrator import agent_orchestrator
from app.services.content_service import content_service


class QuizService:
    """Service for managing quizzes and quiz results."""
    
    def __init__(self):
        """Initialize the quiz service with in-memory storage."""
        self._quizzes: dict[str, Quiz] = {}
        self._results: dict[str, QuizResult] = {}
        self._quiz_results: dict[str, list[str]] = {}  # quiz_id -> list of result_ids
    
    def generate_quiz(self, user_id: str, topic: Optional[str] = None,
                      content_id: Optional[str] = None,
                      question_count: int = 5) -> tuple[Optional[Quiz], Optional[str]]:
        """
        Generate a quiz from a topic or content.
        
        Args:
            user_id: ID of the user requesting the quiz.
            topic: Optional topic for the quiz.
            content_id: Optional content ID to base questions on.
            question_count: Number of questions to generate.
            
        Returns:
            Tuple of (Quiz, error_message). Quiz is None if error occurred.
        """
        if not topic and not content_id:
            return None, "Either topic or contentId must be provided"
        
        if question_count < 1:
            return None, "Question count must be at least 1"
        
        if question_count > 20:
            return None, "Question count cannot exceed 20"
        
        # Get content summary if content_id provided
        content_summary = None
        if content_id:
            content = content_service.get_content(content_id)
            if not content:
                return None, "Content not found"
            if content.user_id != user_id:
                return None, "Not authorized to access this content"
            # Build content summary from key points
            if content.key_points:
                content_summary = ". ".join(content.key_points)
            elif content.summary:
                content_summary = ". ".join(content.summary)
        
        # Generate questions using QuizAgent
        raw_questions = agent_orchestrator.generate_quiz(
            topic=topic,
            content=content_summary,
            question_count=question_count
        )
        
        if not raw_questions:
            return None, "Failed to generate quiz questions"
        
        # Convert to QuizQuestion objects
        questions = []
        for i, q in enumerate(raw_questions):
            question = QuizQuestion(
                id=q.get("id", f"q{i+1}"),
                question=q.get("question", ""),
                options=q.get("options", []),
                correct_index=q.get("correct_index", 0),
                explanation=q.get("explanation", "")
            )
            
            # Validate question structure
            if question.is_valid():
                questions.append(question)
        
        if not questions:
            return None, "Failed to generate valid quiz questions"
        
        # Create quiz
        quiz = Quiz.create(
            user_id=user_id,
            questions=questions,
            topic=topic,
            content_id=content_id
        )
        
        # Store quiz
        self._quizzes[quiz.id] = quiz
        
        return quiz, None
    
    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get a quiz by ID."""
        return self._quizzes.get(quiz_id)
    
    def get_user_quizzes(self, user_id: str) -> list[Quiz]:
        """Get all quizzes for a user."""
        return [q for q in self._quizzes.values() if q.user_id == user_id]
    
    def submit_quiz(self, quiz_id: str, user_id: str, 
                    answers: list[int]) -> tuple[Optional[QuizResult], Optional[str]]:
        """
        Submit quiz answers and calculate results.
        
        Args:
            quiz_id: ID of the quiz being submitted.
            user_id: ID of the user submitting.
            answers: List of answer indices.
            
        Returns:
            Tuple of (QuizResult, error_message). Result is None if error occurred.
        """
        quiz = self._quizzes.get(quiz_id)
        
        if not quiz:
            return None, "Quiz not found"
        
        if quiz.user_id != user_id:
            return None, "Not authorized to submit this quiz"
        
        # Validate answers
        if len(answers) != len(quiz.questions):
            return None, f"Expected {len(quiz.questions)} answers, got {len(answers)}"
        
        # Validate answer indices
        for i, answer in enumerate(answers):
            if answer < 0 or answer >= len(quiz.questions[i].options):
                return None, f"Answer index {answer} out of range for question {i+1}"
        
        # Check if quiz already submitted
        existing_results = self._quiz_results.get(quiz_id, [])
        for result_id in existing_results:
            result = self._results.get(result_id)
            if result and result.user_id == user_id:
                return None, "Quiz has already been submitted"
        
        # Create result
        result = QuizResult.create(
            quiz_id=quiz_id,
            user_id=user_id,
            answers=answers,
            questions=quiz.questions
        )
        
        # Store result
        self._results[result.id] = result
        if quiz_id not in self._quiz_results:
            self._quiz_results[quiz_id] = []
        self._quiz_results[quiz_id].append(result.id)
        
        return result, None
    
    def get_result(self, result_id: str) -> Optional[QuizResult]:
        """Get a quiz result by ID."""
        return self._results.get(result_id)
    
    def get_quiz_results(self, quiz_id: str) -> list[QuizResult]:
        """Get all results for a quiz."""
        result_ids = self._quiz_results.get(quiz_id, [])
        return [self._results[rid] for rid in result_ids if rid in self._results]
    
    def get_user_results(self, user_id: str) -> list[QuizResult]:
        """Get all quiz results for a user."""
        return [r for r in self._results.values() if r.user_id == user_id]
    
    def get_answer(self, quiz_id: str, user_id: str, 
                   question_index: int) -> Optional[int]:
        """
        Get a recorded answer for a specific question.
        
        Args:
            quiz_id: ID of the quiz.
            user_id: ID of the user.
            question_index: Index of the question.
            
        Returns:
            The recorded answer index, or None if not found.
        """
        result_ids = self._quiz_results.get(quiz_id, [])
        for result_id in result_ids:
            result = self._results.get(result_id)
            if result and result.user_id == user_id:
                if 0 <= question_index < len(result.answers):
                    return result.answers[question_index]
        return None
    
    def calculate_score(self, answers: list[int], 
                        questions: list[QuizQuestion]) -> tuple[int, int, float]:
        """
        Calculate quiz score from answers.
        
        Args:
            answers: List of answer indices.
            questions: List of quiz questions.
            
        Returns:
            Tuple of (correct_count, total_questions, score_percentage).
        """
        total = len(questions)
        correct = 0
        
        for i, answer in enumerate(answers):
            if i < len(questions) and answer == questions[i].correct_index:
                correct += 1
        
        score = (correct / total) if total > 0 else 0.0
        return correct, total, score
    
    def clear_all(self) -> None:
        """Clear all quizzes and results (for testing)."""
        self._quizzes.clear()
        self._results.clear()
        self._quiz_results.clear()


# Global quiz service instance
quiz_service = QuizService()
