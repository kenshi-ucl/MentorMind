"""Progress service for tracking and calculating user learning progress."""
from typing import Optional
from app.models.progress import UserProgress, TopicProgress, ProgressEntry
from app.services.quiz_service import quiz_service


class ProgressService:
    """Service for managing user progress tracking."""
    
    def __init__(self):
        """Initialize the progress service."""
        # Progress is calculated dynamically from quiz results
        pass
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """
        Get progress data for a user.
        
        Calculates progress from quiz results including:
        - Total quizzes taken
        - Overall success rate
        - Topics mastered (>= 80% success rate)
        - Topics needing work (< 50% success rate)
        - Progress over time
        
        Args:
            user_id: ID of the user.
            
        Returns:
            UserProgress object with calculated metrics.
        """
        # Get all quiz results for the user
        results = quiz_service.get_user_results(user_id)
        
        # Initialize progress
        progress = UserProgress(user_id=user_id)
        
        if not results:
            return progress
        
        # Calculate totals and build topic progress
        topics: dict[str, TopicProgress] = {}
        history: list[ProgressEntry] = []
        
        for result in results:
            # Update totals
            progress.total_quizzes += 1
            progress.total_questions += result.total_questions
            progress.correct_answers += result.correct_count
            
            # Get quiz to find topic
            quiz = quiz_service.get_quiz(result.quiz_id)
            topic = quiz.topic if quiz else None
            
            # Add to history
            history.append(ProgressEntry(
                date=result.completed_at,
                quiz_id=result.quiz_id,
                score=result.score * 100,  # Convert to percentage
                topic=topic
            ))
            
            # Update topic progress if topic exists
            if topic:
                if topic not in topics:
                    topics[topic] = TopicProgress(
                        topic=topic,
                        attempts=0,
                        correct=0,
                        total_questions=0
                    )
                
                topics[topic].attempts += 1
                topics[topic].correct += result.correct_count
                topics[topic].total_questions += result.total_questions
        
        # Sort history by date
        history.sort(key=lambda x: x.date if x.date else 0)
        
        progress.topics_attempted = topics
        progress.history = history
        
        return progress
    
    def calculate_success_rate(self, correct: int, total: int) -> float:
        """
        Calculate success rate as a percentage.
        
        Args:
            correct: Number of correct answers.
            total: Total number of questions.
            
        Returns:
            Success rate from 0.0 to 100.0, rounded to 1 decimal place.
        """
        if total == 0:
            return 0.0
        return round((correct / total) * 100, 1)
    
    def categorize_topic_mastery(self, success_rate: float) -> str:
        """
        Categorize a topic based on success rate.
        
        Args:
            success_rate: Success rate as a percentage (0-100).
            
        Returns:
            Category string: "mastered", "needs_work", or "in_progress".
        """
        if success_rate >= 80.0:
            return "mastered"
        elif success_rate < 50.0:
            return "needs_work"
        else:
            return "in_progress"
    
    def get_topics_mastered(self, topics: dict[str, TopicProgress]) -> list[str]:
        """
        Get list of topics with success rate >= 80%.
        
        Args:
            topics: Dictionary of topic name to TopicProgress.
            
        Returns:
            List of mastered topic names.
        """
        return [
            topic for topic, progress in topics.items()
            if progress.success_rate >= 80.0
        ]
    
    def get_topics_needing_work(self, topics: dict[str, TopicProgress]) -> list[str]:
        """
        Get list of topics with success rate < 50%.
        
        Args:
            topics: Dictionary of topic name to TopicProgress.
            
        Returns:
            List of topic names needing improvement.
        """
        return [
            topic for topic, progress in topics.items()
            if progress.success_rate < 50.0
        ]


# Global progress service instance
progress_service = ProgressService()
