"""Demo seed data for MentorMind AI Tutor.

This module provides example user accounts, sample lesson content, and quiz examples
for demonstration purposes.

Requirements: 10.1, 10.2
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.models.user import User
from app.models.content import Content
from app.models.quiz import Quiz, QuizQuestion, QuizResult
from app.models.progress import UserProgress, TopicProgress, ProgressEntry
from app.services.auth_service import auth_service
from app.services.quiz_service import quiz_service
from app.services.content_service import content_service


# Demo user accounts
DEMO_USERS = [
    {
        "email": "demo@mentormind.ai",
        "password": "demo123",
        "name": "Demo User"
    },
    {
        "email": "student@example.com",
        "password": "student123",
        "name": "Alex Student"
    },
    {
        "email": "teacher@example.com",
        "password": "teacher123",
        "name": "Dr. Sarah Teacher"
    }
]

# Sample lesson content with key points
SAMPLE_LESSONS = [
    {
        "title": "Introduction to Python Programming",
        "filename": "intro_python.pdf",
        "file_type": "pdf",
        "summary": [
            "Python is a high-level, interpreted programming language known for its simplicity and readability.",
            "Key features include dynamic typing, automatic memory management, and extensive standard library."
        ],
        "key_points": [
            "Python uses indentation for code blocks instead of braces",
            "Variables don't need explicit type declarations",
            "Lists, dictionaries, and tuples are fundamental data structures",
            "Functions are defined using the 'def' keyword",
            "Python supports object-oriented, functional, and procedural programming paradigms"
        ]
    },
    {
        "title": "Machine Learning Fundamentals",
        "filename": "ml_basics.pdf",
        "file_type": "pdf",
        "summary": [
            "Machine learning is a subset of AI that enables systems to learn from data.",
            "The three main types are supervised, unsupervised, and reinforcement learning."
        ],
        "key_points": [
            "Supervised learning uses labeled data for training",
            "Unsupervised learning finds patterns in unlabeled data",
            "Neural networks are inspired by biological brain structure",
            "Overfitting occurs when a model memorizes training data",
            "Cross-validation helps evaluate model performance"
        ]
    },
    {
        "title": "Web Development with React",
        "filename": "react_tutorial.pdf",
        "file_type": "pdf",
        "summary": [
            "React is a JavaScript library for building user interfaces.",
            "It uses a component-based architecture and virtual DOM for efficient updates."
        ],
        "key_points": [
            "Components are reusable UI building blocks",
            "Props pass data from parent to child components",
            "State manages component-specific data that can change",
            "Hooks like useState and useEffect manage state and side effects",
            "JSX allows writing HTML-like syntax in JavaScript"
        ]
    }
]

# Sample quiz questions by topic
SAMPLE_QUIZZES = {
    "Python Basics": [
        {
            "question": "What keyword is used to define a function in Python?",
            "options": ["function", "def", "func", "define"],
            "correct_index": 1,
            "explanation": "In Python, functions are defined using the 'def' keyword followed by the function name and parameters."
        },
        {
            "question": "Which data structure uses key-value pairs in Python?",
            "options": ["List", "Tuple", "Dictionary", "Set"],
            "correct_index": 2,
            "explanation": "Dictionaries in Python store data as key-value pairs, allowing fast lookup by key."
        },
        {
            "question": "How do you create a comment in Python?",
            "options": ["// comment", "/* comment */", "# comment", "-- comment"],
            "correct_index": 2,
            "explanation": "Python uses the hash symbol (#) for single-line comments."
        },
        {
            "question": "What is the output of print(type([]))?",
            "options": ["<class 'tuple'>", "<class 'list'>", "<class 'dict'>", "<class 'set'>"],
            "correct_index": 1,
            "explanation": "Empty square brackets [] create an empty list in Python."
        },
        {
            "question": "Which operator is used for exponentiation in Python?",
            "options": ["^", "**", "^^", "exp"],
            "correct_index": 1,
            "explanation": "Python uses ** for exponentiation. For example, 2**3 equals 8."
        }
    ],
    "Machine Learning": [
        {
            "question": "What type of learning uses labeled training data?",
            "options": ["Unsupervised learning", "Reinforcement learning", "Supervised learning", "Transfer learning"],
            "correct_index": 2,
            "explanation": "Supervised learning uses labeled data where the correct output is known during training."
        },
        {
            "question": "What is overfitting in machine learning?",
            "options": [
                "Model performs well on all data",
                "Model memorizes training data but fails on new data",
                "Model is too simple",
                "Model trains too quickly"
            ],
            "correct_index": 1,
            "explanation": "Overfitting occurs when a model learns the training data too well, including noise, and fails to generalize."
        },
        {
            "question": "Which algorithm is commonly used for classification?",
            "options": ["Linear Regression", "K-Means", "Decision Tree", "PCA"],
            "correct_index": 2,
            "explanation": "Decision Trees can be used for both classification and regression tasks."
        },
        {
            "question": "What does CNN stand for in deep learning?",
            "options": [
                "Computer Neural Network",
                "Convolutional Neural Network",
                "Connected Node Network",
                "Computed Neuron Network"
            ],
            "correct_index": 1,
            "explanation": "CNN stands for Convolutional Neural Network, commonly used for image processing."
        },
        {
            "question": "What is the purpose of a validation set?",
            "options": [
                "To train the model",
                "To tune hyperparameters and prevent overfitting",
                "To deploy the model",
                "To collect more data"
            ],
            "correct_index": 1,
            "explanation": "A validation set is used to tune hyperparameters and evaluate model performance during training."
        }
    ],
    "React Development": [
        {
            "question": "What hook is used to manage state in functional components?",
            "options": ["useEffect", "useState", "useContext", "useReducer"],
            "correct_index": 1,
            "explanation": "useState is the primary hook for managing local state in React functional components."
        },
        {
            "question": "What is JSX?",
            "options": [
                "A JavaScript framework",
                "A syntax extension for JavaScript that looks like HTML",
                "A CSS preprocessor",
                "A testing library"
            ],
            "correct_index": 1,
            "explanation": "JSX is a syntax extension that allows writing HTML-like code in JavaScript files."
        },
        {
            "question": "How do you pass data from parent to child component?",
            "options": ["Using state", "Using props", "Using context", "Using refs"],
            "correct_index": 1,
            "explanation": "Props (properties) are used to pass data from parent components to child components."
        },
        {
            "question": "What does the useEffect hook do?",
            "options": [
                "Manages component state",
                "Handles side effects like API calls and subscriptions",
                "Creates new components",
                "Styles components"
            ],
            "correct_index": 1,
            "explanation": "useEffect handles side effects in functional components, like data fetching and DOM manipulation."
        },
        {
            "question": "What is the Virtual DOM?",
            "options": [
                "A copy of the real DOM that React uses for efficient updates",
                "A browser feature",
                "A CSS framework",
                "A testing environment"
            ],
            "correct_index": 0,
            "explanation": "The Virtual DOM is a lightweight copy of the real DOM that React uses to minimize actual DOM updates."
        }
    ]
}


class SeedDataService:
    """Service for seeding demo data into the application."""
    
    def __init__(self):
        """Initialize the seed data service."""
        self._seeded = False
        self._demo_user_ids: dict[str, str] = {}  # email -> user_id
        self._demo_content_ids: list[str] = []
        self._demo_quiz_ids: list[str] = []
    
    def seed_all(self) -> dict:
        """
        Seed all demo data into the application.
        
        Returns:
            Dictionary with seeding results.
        """
        if self._seeded:
            return {"status": "already_seeded", "message": "Demo data has already been seeded"}
        
        results = {
            "users": self.seed_users(),
            "content": self.seed_content(),
            "quizzes": self.seed_quizzes()
        }
        
        self._seeded = True
        return {"status": "success", "results": results}
    
    def seed_users(self) -> list[dict]:
        """
        Seed demo user accounts.
        
        Returns:
            List of created user info.
        """
        created_users = []
        
        for user_data in DEMO_USERS:
            # Check if user already exists
            existing = auth_service.get_user_by_email(user_data["email"])
            if existing:
                self._demo_user_ids[user_data["email"]] = existing.id
                created_users.append({
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "status": "already_exists",
                    "id": existing.id
                })
                continue
            
            # Register new user
            user, error = auth_service.register(
                email=user_data["email"],
                password=user_data["password"],
                name=user_data["name"]
            )
            
            if user:
                self._demo_user_ids[user_data["email"]] = user.id
                created_users.append({
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "status": "created",
                    "id": user.id
                })
            else:
                created_users.append({
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "status": "error",
                    "error": error
                })
        
        return created_users
    
    def seed_content(self) -> list[dict]:
        """
        Seed sample lesson content.
        
        Returns:
            List of created content info.
        """
        created_content = []
        
        # Use demo user for content
        demo_user_id = self._demo_user_ids.get("demo@mentormind.ai")
        if not demo_user_id:
            return [{"status": "error", "error": "Demo user not found"}]
        
        for lesson in SAMPLE_LESSONS:
            # Create content record directly (without actual file)
            content = Content(
                id=str(uuid.uuid4()),
                user_id=demo_user_id,
                filename=lesson["filename"],
                file_type=lesson["file_type"],
                file_path=f"/demo/{lesson['filename']}",
                summary=lesson["summary"],
                key_points=lesson["key_points"],
                processed_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            
            # Store in content service
            content_service._contents[content.id] = content
            if demo_user_id not in content_service._user_contents:
                content_service._user_contents[demo_user_id] = []
            content_service._user_contents[demo_user_id].append(content.id)
            
            self._demo_content_ids.append(content.id)
            created_content.append({
                "title": lesson["title"],
                "filename": lesson["filename"],
                "id": content.id,
                "status": "created"
            })
        
        return created_content
    
    def seed_quizzes(self) -> list[dict]:
        """
        Seed sample quizzes with results for progress tracking.
        
        Returns:
            List of created quiz info.
        """
        created_quizzes = []
        
        # Use demo user for quizzes
        demo_user_id = self._demo_user_ids.get("demo@mentormind.ai")
        if not demo_user_id:
            return [{"status": "error", "error": "Demo user not found"}]
        
        # Create quizzes for each topic
        for topic, questions_data in SAMPLE_QUIZZES.items():
            # Create quiz questions
            questions = []
            for i, q_data in enumerate(questions_data):
                question = QuizQuestion(
                    id=f"demo_q_{topic.lower().replace(' ', '_')}_{i+1}",
                    question=q_data["question"],
                    options=q_data["options"],
                    correct_index=q_data["correct_index"],
                    explanation=q_data["explanation"]
                )
                questions.append(question)
            
            # Create quiz
            quiz = Quiz(
                id=str(uuid.uuid4()),
                user_id=demo_user_id,
                topic=topic,
                content_id=None,
                questions=questions,
                created_at=datetime.utcnow() - timedelta(days=7)
            )
            
            # Store quiz
            quiz_service._quizzes[quiz.id] = quiz
            self._demo_quiz_ids.append(quiz.id)
            
            # Create a sample result (simulate user taking the quiz)
            # Vary the scores to show different mastery levels
            if topic == "Python Basics":
                # High score - mastered
                answers = [1, 2, 2, 1, 1]  # All correct
            elif topic == "Machine Learning":
                # Medium score - in progress
                answers = [2, 1, 2, 0, 1]  # 3 correct
            else:
                # Lower score - needs work
                answers = [0, 1, 0, 1, 0]  # 2 correct
            
            result = QuizResult.create(
                quiz_id=quiz.id,
                user_id=demo_user_id,
                answers=answers,
                questions=questions
            )
            result.completed_at = datetime.utcnow() - timedelta(days=5)
            
            # Store result
            quiz_service._results[result.id] = result
            if quiz.id not in quiz_service._quiz_results:
                quiz_service._quiz_results[quiz.id] = []
            quiz_service._quiz_results[quiz.id].append(result.id)
            
            created_quizzes.append({
                "topic": topic,
                "quiz_id": quiz.id,
                "questions_count": len(questions),
                "result_score": result.score,
                "status": "created"
            })
        
        return created_quizzes
    
    def get_demo_credentials(self) -> list[dict]:
        """
        Get demo user credentials for display.
        
        Returns:
            List of demo credentials (email and password).
        """
        return [
            {"email": user["email"], "password": user["password"], "name": user["name"]}
            for user in DEMO_USERS
        ]
    
    def is_seeded(self) -> bool:
        """Check if demo data has been seeded."""
        return self._seeded
    
    def reset(self) -> None:
        """Reset seed data state (for testing)."""
        self._seeded = False
        self._demo_user_ids.clear()
        self._demo_content_ids.clear()
        self._demo_quiz_ids.clear()


# Global seed data service instance
seed_data_service = SeedDataService()


def seed_demo_data() -> dict:
    """
    Convenience function to seed all demo data.
    
    Returns:
        Dictionary with seeding results.
    """
    return seed_data_service.seed_all()


def get_demo_credentials() -> list[dict]:
    """
    Convenience function to get demo credentials.
    
    Returns:
        List of demo credentials.
    """
    return seed_data_service.get_demo_credentials()
