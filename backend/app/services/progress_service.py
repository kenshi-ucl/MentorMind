"""
Progress service for tracking and calculating user learning progress.

Uses SQLAlchemy for database persistence of quiz results and progress tracking.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict

from app.database import db
from app.models.quiz_result import QuizResult


class ProgressService:
    """Service for managing user progress tracking with database persistence."""
    
    def record_quiz_result(
        self,
        user_id: str,
        quiz_id: str,
        topic: Optional[str],
        score: int,
        total_questions: int,
        answers: Optional[Dict[str, Any]] = None
    ) -> QuizResult:
        """
        Record a quiz result in the database.
        
        Args:
            user_id: ID of the user who completed the quiz
            quiz_id: ID of the quiz
            topic: Topic of the quiz (optional)
            score: Number of correct answers
            total_questions: Total number of questions
            answers: Dictionary of question IDs to user answers (optional)
            
        Returns:
            The created QuizResult object
        """
        result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            topic=topic,
            score=score,
            total_questions=total_questions
        )
        
        if answers:
            result.answers = answers
        
        db.session.add(result)
        db.session.commit()
        
        return result
    
    def get_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Get aggregated progress for a user.
        
        Calculates progress metrics from stored quiz results including:
        - Total quizzes taken
        - Total questions answered
        - Correct answers count
        - Overall success rate
        - Topic-wise progress
        - Recent activity
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing progress metrics
        """
        results = QuizResult.query.filter_by(user_id=user_id).all()
        
        if not results:
            return {
                'totalQuizzes': 0,
                'totalQuestions': 0,
                'correctAnswers': 0,
                'successRate': 0.0,
                'topicProgress': {},
                'recentActivity': []
            }
        
        total_questions = sum(r.total_questions for r in results)
        correct_answers = sum(r.score for r in results)
        
        # Calculate topic-wise progress
        topic_stats = defaultdict(lambda: {'correct': 0, 'total': 0, 'quizzes': 0})
        for r in results:
            if r.topic:
                topic_stats[r.topic]['correct'] += r.score
                topic_stats[r.topic]['total'] += r.total_questions
                topic_stats[r.topic]['quizzes'] += 1
        
        topic_progress = {}
        for topic, stats in topic_stats.items():
            percentage = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            topic_progress[topic] = {
                'percentage': round(percentage, 1),
                'quizzes': stats['quizzes'],
                'correct': stats['correct'],
                'total': stats['total']
            }
        
        # Get recent activity (last 10 results, sorted by date descending)
        recent = sorted(results, key=lambda r: r.created_at or datetime.min, reverse=True)[:10]
        recent_activity = [{
            'quizId': r.quiz_id,
            'topic': r.topic,
            'score': r.score,
            'total': r.total_questions,
            'percentage': r.percentage,
            'date': r.created_at.isoformat() if r.created_at else None
        } for r in recent]
        
        # Calculate overall success rate
        success_rate = round((correct_answers / total_questions * 100), 1) if total_questions > 0 else 0.0
        
        return {
            'totalQuizzes': len(results),
            'totalQuestions': total_questions,
            'correctAnswers': correct_answers,
            'successRate': success_rate,
            'topicProgress': topic_progress,
            'recentActivity': recent_activity
        }
    
    def get_quiz_results(self, user_id: str) -> List[QuizResult]:
        """
        Get all quiz results for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of QuizResult objects
        """
        return QuizResult.query.filter_by(user_id=user_id).order_by(
            QuizResult.created_at.desc()
        ).all()
    
    def get_quiz_result(self, result_id: str, user_id: str) -> Optional[QuizResult]:
        """
        Get a specific quiz result if owned by user.
        
        Args:
            result_id: ID of the quiz result
            user_id: ID of the user
            
        Returns:
            QuizResult if found and owned by user, None otherwise
        """
        return QuizResult.query.filter_by(id=result_id, user_id=user_id).first()
    
    def calculate_success_rate(self, correct: int, total: int) -> float:
        """
        Calculate success rate as a percentage.
        
        Args:
            correct: Number of correct answers
            total: Total number of questions
            
        Returns:
            Success rate from 0.0 to 100.0, rounded to 1 decimal place
        """
        if total == 0:
            return 0.0
        return round((correct / total) * 100, 1)
    
    def categorize_topic_mastery(self, success_rate: float) -> str:
        """
        Categorize a topic based on success rate.
        
        Args:
            success_rate: Success rate as a percentage (0-100)
            
        Returns:
            Category string: "mastered", "needs_work", or "in_progress"
        """
        if success_rate >= 80.0:
            return "mastered"
        elif success_rate < 50.0:
            return "needs_work"
        else:
            return "in_progress"
    
    def get_topics_mastered(self, user_id: str) -> List[str]:
        """
        Get list of topics with success rate >= 80%.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of mastered topic names
        """
        progress = self.get_progress(user_id)
        return [
            topic for topic, data in progress['topicProgress'].items()
            if data['percentage'] >= 80.0
        ]
    
    def get_topics_needing_work(self, user_id: str) -> List[str]:
        """
        Get list of topics with success rate < 50%.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of topic names needing improvement
        """
        progress = self.get_progress(user_id)
        return [
            topic for topic, data in progress['topicProgress'].items()
            if data['percentage'] < 50.0
        ]


# Global progress service instance
progress_service = ProgressService()
