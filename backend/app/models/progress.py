"""Progress models for tracking user learning progress."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TopicProgress:
    """Model representing progress for a specific topic."""
    
    topic: str
    attempts: int
    correct: int
    total_questions: int
    
    @property
    def mastery_level(self) -> float:
        """Calculate mastery level as a ratio (0.0 to 1.0)."""
        if self.total_questions == 0:
            return 0.0
        return self.correct / self.total_questions
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage (0.0 to 100.0)."""
        return self.mastery_level * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "topic": self.topic,
            "attempts": self.attempts,
            "correct": self.correct,
            "totalQuestions": self.total_questions,
            "masteryLevel": self.mastery_level,
            "successRate": round(self.success_rate, 1)
        }


@dataclass
class ProgressEntry:
    """Model representing a single progress entry (quiz result)."""
    
    date: datetime
    quiz_id: str
    score: float
    topic: Optional[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "quizId": self.quiz_id,
            "score": self.score,
            "topic": self.topic
        }


@dataclass
class UserProgress:
    """Model representing overall user progress."""
    
    user_id: str
    total_quizzes: int = 0
    total_questions: int = 0
    correct_answers: int = 0
    topics_attempted: dict[str, TopicProgress] = field(default_factory=dict)
    history: list[ProgressEntry] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """
        Calculate overall success rate as a percentage.
        
        Returns:
            Success rate from 0.0 to 100.0, rounded to 1 decimal place.
        """
        if self.total_questions == 0:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 1)
    
    @property
    def topics_mastered(self) -> list[str]:
        """
        Get list of topics with mastery level >= 80%.
        
        Returns:
            List of topic names that are considered mastered.
        """
        return [
            topic for topic, progress in self.topics_attempted.items()
            if progress.success_rate >= 80.0
        ]
    
    @property
    def topics_needing_work(self) -> list[str]:
        """
        Get list of topics with mastery level < 50%.
        
        Returns:
            List of topic names that need improvement.
        """
        return [
            topic for topic, progress in self.topics_attempted.items()
            if progress.success_rate < 50.0
        ]
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "userId": self.user_id,
            "totalQuizzes": self.total_quizzes,
            "totalQuestions": self.total_questions,
            "correctAnswers": self.correct_answers,
            "successRate": self.success_rate,
            "topicsMastered": self.topics_mastered,
            "topicsNeedingWork": self.topics_needing_work,
            "topicsAttempted": {
                topic: progress.to_dict() 
                for topic, progress in self.topics_attempted.items()
            },
            "progressOverTime": [entry.to_dict() for entry in self.history]
        }
