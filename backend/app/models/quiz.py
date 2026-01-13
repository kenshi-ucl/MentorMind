"""Quiz models for quiz generation and results."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class QuizQuestion:
    """Model representing a single quiz question."""
    
    id: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str
    
    def to_dict(self) -> dict:
        """Convert question to dictionary representation."""
        return {
            "id": self.id,
            "question": self.question,
            "options": self.options,
            "correctIndex": self.correct_index,
            "explanation": self.explanation
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuizQuestion":
        """Create QuizQuestion instance from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            question=data["question"],
            options=data["options"],
            correct_index=data.get("correctIndex", data.get("correct_index", 0)),
            explanation=data.get("explanation", "")
        )
    
    def is_valid(self) -> bool:
        """Check if the question structure is valid."""
        return (
            bool(self.question) and
            len(self.options) >= 2 and
            0 <= self.correct_index < len(self.options) and
            bool(self.explanation)
        )


@dataclass
class Quiz:
    """Model representing a quiz."""
    
    id: str
    user_id: str
    topic: Optional[str]
    content_id: Optional[str]
    questions: list[QuizQuestion]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(cls, user_id: str, questions: list[QuizQuestion],
               topic: Optional[str] = None, 
               content_id: Optional[str] = None) -> "Quiz":
        """Create a new Quiz instance."""
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            content_id=content_id,
            questions=questions,
            created_at=datetime.utcnow()
        )
    
    def to_dict(self) -> dict:
        """Convert quiz to dictionary representation."""
        return {
            "id": self.id,
            "userId": self.user_id,
            "topic": self.topic,
            "contentId": self.content_id,
            "questions": [q.to_dict() for q in self.questions],
            "createdAt": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Quiz":
        """Create Quiz instance from dictionary."""
        created_at = datetime.utcnow()
        if data.get("createdAt"):
            created_at = datetime.fromisoformat(data["createdAt"])
        
        questions = [
            QuizQuestion.from_dict(q) for q in data.get("questions", [])
        ]
        
        return cls(
            id=data["id"],
            user_id=data.get("userId", data.get("user_id")),
            topic=data.get("topic"),
            content_id=data.get("contentId", data.get("content_id")),
            questions=questions,
            created_at=created_at
        )


@dataclass
class QuizResult:
    """Model representing a quiz submission result."""
    
    id: str
    quiz_id: str
    user_id: str
    answers: list[int]
    score: float
    total_questions: int
    correct_count: int
    completed_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(cls, quiz_id: str, user_id: str, answers: list[int],
               questions: list[QuizQuestion]) -> "QuizResult":
        """
        Create a new QuizResult by calculating score from answers.
        
        Args:
            quiz_id: ID of the quiz.
            user_id: ID of the user.
            answers: List of answer indices submitted by user.
            questions: List of quiz questions for score calculation.
        """
        total = len(questions)
        correct = 0
        
        for i, answer in enumerate(answers):
            if i < len(questions) and answer == questions[i].correct_index:
                correct += 1
        
        score = (correct / total) if total > 0 else 0.0
        
        return cls(
            id=str(uuid.uuid4()),
            quiz_id=quiz_id,
            user_id=user_id,
            answers=answers,
            score=score,
            total_questions=total,
            correct_count=correct,
            completed_at=datetime.utcnow()
        )
    
    def to_dict(self) -> dict:
        """Convert result to dictionary representation."""
        return {
            "id": self.id,
            "quizId": self.quiz_id,
            "userId": self.user_id,
            "answers": self.answers,
            "score": self.score,
            "totalQuestions": self.total_questions,
            "correctCount": self.correct_count,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QuizResult":
        """Create QuizResult instance from dictionary."""
        completed_at = datetime.utcnow()
        if data.get("completedAt"):
            completed_at = datetime.fromisoformat(data["completedAt"])
        
        return cls(
            id=data["id"],
            quiz_id=data.get("quizId", data.get("quiz_id")),
            user_id=data.get("userId", data.get("user_id")),
            answers=data["answers"],
            score=data["score"],
            total_questions=data.get("totalQuestions", data.get("total_questions")),
            correct_count=data.get("correctCount", data.get("correct_count")),
            completed_at=completed_at
        )
