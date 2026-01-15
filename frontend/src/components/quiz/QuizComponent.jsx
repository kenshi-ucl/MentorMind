import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';
import { useAuth } from '../../context/AuthContext';

const API_BASE = 'http://localhost:5000/api';

/**
 * QuizComponent for displaying and managing quiz interactions.
 * 
 * Features:
 * - Display questions one at a time
 * - Selectable answer options
 * - Immediate feedback on answer selection
 * - Score display on completion
 * - Explanations for incorrect answers
 * 
 * Requirements: 6.2, 6.3, 6.4
 */
export function QuizComponent({ topic = null, contentId = null, questionCount = 5, onComplete = null }) {
  const { token } = useAuth();
  const [quizState, setQuizState] = useState({
    status: 'idle', // 'idle' | 'loading' | 'active' | 'completed'
    quizId: null,
    questions: [],
    currentIndex: 0,
    answers: [],
    selectedAnswer: null,
    showFeedback: false,
    results: null,
    questionResults: [], // Track results for each question as we go
    error: null,
  });

  /**
   * Generate a new quiz from the API
   */
  const generateQuiz = async () => {
    if (!topic && !contentId) {
      setQuizState(prev => ({
        ...prev,
        error: 'Please provide a topic or content to generate a quiz.',
      }));
      return;
    }

    setQuizState(prev => ({
      ...prev,
      status: 'loading',
      error: null,
    }));

    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/quiz/generate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          topic,
          contentId,
          questionCount,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate quiz');
      }

      setQuizState(prev => ({
        ...prev,
        status: 'active',
        quizId: data.quizId,
        questions: data.questions,
        currentIndex: 0,
        answers: new Array(data.questions.length).fill(null),
        selectedAnswer: null,
        showFeedback: false,
        questionResults: [], // Reset question results
        error: null,
      }));
    } catch (err) {
      setQuizState(prev => ({
        ...prev,
        status: 'idle',
        error: err.message || 'Failed to generate quiz. Please try again.',
      }));
    }
  };

  /**
   * Handle answer selection
   */
  const selectAnswer = (answerIndex) => {
    if (quizState.showFeedback) return; // Don't allow changing answer after feedback shown

    setQuizState(prev => ({
      ...prev,
      selectedAnswer: answerIndex,
    }));
  };

  /**
   * Confirm the selected answer and move to next question (no immediate feedback)
   */
  const confirmAnswer = () => {
    if (quizState.selectedAnswer === null) return;

    const newAnswers = [...quizState.answers];
    newAnswers[quizState.currentIndex] = quizState.selectedAnswer;

    const { currentIndex, questions } = quizState;

    if (currentIndex < questions.length - 1) {
      // Move to next question immediately
      setQuizState(prev => ({
        ...prev,
        answers: newAnswers,
        currentIndex: prev.currentIndex + 1,
        selectedAnswer: prev.answers[prev.currentIndex + 1],
      }));
    } else {
      // Last question - store answer and submit
      setQuizState(prev => ({
        ...prev,
        answers: newAnswers,
      }));
      // Submit quiz with the new answers
      submitQuizWithAnswers(newAnswers);
    }
  };

  /**
   * Submit the quiz with provided answers
   */
  const submitQuizWithAnswers = async (finalAnswers) => {
    setQuizState(prev => ({
      ...prev,
      status: 'loading',
    }));

    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/quiz/submit`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          quizId: quizState.quizId,
          answers: finalAnswers,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to submit quiz');
      }

      setQuizState(prev => ({
        ...prev,
        status: 'completed',
        results: data,
      }));

      // Call onComplete callback if provided
      if (onComplete) {
        onComplete(data);
      }
    } catch (err) {
      setQuizState(prev => ({
        ...prev,
        status: 'active',
        error: err.message || 'Failed to submit quiz. Please try again.',
      }));
    }
  };

  /**
   * Move to the previous question
   */
  const prevQuestion = () => {
    if (quizState.currentIndex > 0) {
      setQuizState(prev => ({
        ...prev,
        currentIndex: prev.currentIndex - 1,
        selectedAnswer: prev.answers[prev.currentIndex - 1],
      }));
    }
  };

  /**
   * Reset quiz to start over
   */
  const resetQuiz = () => {
    setQuizState({
      status: 'idle',
      quizId: null,
      questions: [],
      currentIndex: 0,
      answers: [],
      selectedAnswer: null,
      showFeedback: false,
      results: null,
      questionResults: [],
      error: null,
    });
  };

  // Render based on quiz status
  const { status, questions, currentIndex, selectedAnswer, showFeedback, results, error } = quizState;

  // Idle state - show start button
  if (status === 'idle') {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Quiz Time!</CardTitle>
          <CardDescription>
            {topic ? `Topic: ${topic}` : 'Test your knowledge'}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center py-8">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
            <svg
              className="w-10 h-10 text-indigo-600 dark:text-indigo-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Ready to test your understanding? This quiz has {questionCount} questions.
          </p>
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm">
              {error}
            </div>
          )}
        </CardContent>
        <CardFooter className="justify-center">
          <Button onClick={generateQuiz} size="lg">
            Start Quiz
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // Loading state
  if (status === 'loading') {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="py-12 text-center">
          <div className="flex flex-col items-center">
            <svg
              className="w-12 h-12 text-indigo-600 dark:text-indigo-400 animate-spin mb-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-gray-600 dark:text-gray-400">
              {quizState.quizId ? 'Submitting quiz...' : 'Generating quiz...'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Completed state - show results
  if (status === 'completed' && results) {
    return (
      <QuizResults
        results={results}
        onRetry={resetQuiz}
      />
    );
  }

  // Active state - show current question
  const currentQuestion = questions[currentIndex];

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Question {currentIndex + 1} of {questions.length}</CardTitle>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {topic && `Topic: ${topic}`}
          </span>
        </div>
        {/* Progress bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-2">
          <div
            className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
          />
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}
        
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          {currentQuestion.question}
        </h3>

        <div className="space-y-3">
          {currentQuestion.options.map((option, index) => (
            <AnswerOption
              key={index}
              index={index}
              option={option}
              isSelected={selectedAnswer === index}
              showFeedback={false}
              isCorrect={false}
              onClick={() => selectAnswer(index)}
              disabled={false}
            />
          ))}
        </div>

        {/* No per-question feedback - results shown at end */}
      </CardContent>
      <CardFooter className="justify-between">
        <div className="flex items-center gap-2">
          {currentIndex > 0 && (
            <Button variant="outline" onClick={prevQuestion}>
              Previous
            </Button>
          )}
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {quizState.answers.filter(a => a !== null).length} of {questions.length} answered
          </span>
        </div>
        <Button
          onClick={confirmAnswer}
          disabled={selectedAnswer === null}
        >
          {currentIndex < questions.length - 1 ? 'Next Question' : 'Submit Quiz'}
        </Button>
      </CardFooter>
    </Card>
  );
}


/**
 * Individual answer option component
 */
function AnswerOption({ index, option, isSelected, showFeedback, isCorrect, onClick, disabled }) {
  const getOptionStyles = () => {
    if (!showFeedback) {
      return isSelected
        ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20'
        : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700';
    }

    // Show feedback styles
    if (isCorrect) {
      return 'border-green-500 bg-green-50 dark:bg-green-900/20';
    }
    if (isSelected && !isCorrect) {
      return 'border-red-500 bg-red-50 dark:bg-red-900/20';
    }
    return 'border-gray-200 dark:border-gray-700 opacity-50';
  };

  const getLetterStyles = () => {
    if (!showFeedback) {
      return isSelected
        ? 'bg-indigo-600 text-white'
        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';
    }

    if (isCorrect) {
      return 'bg-green-500 text-white';
    }
    if (isSelected && !isCorrect) {
      return 'bg-red-500 text-white';
    }
    return 'bg-gray-100 dark:bg-gray-800 text-gray-400';
  };

  const letters = ['A', 'B', 'C', 'D', 'E', 'F'];

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`w-full p-4 rounded-lg border-2 transition-all duration-200 text-left flex items-center gap-3 ${getOptionStyles()} ${
        disabled ? 'cursor-default' : 'cursor-pointer'
      }`}
      aria-label={`Option ${letters[index]}: ${option}`}
      data-testid={`answer-option-${index}`}
    >
      <span
        className={`w-8 h-8 rounded-full flex items-center justify-center font-medium text-sm ${getLetterStyles()}`}
      >
        {letters[index]}
      </span>
      <span className="flex-1 text-gray-900 dark:text-white">{option}</span>
      {showFeedback && isCorrect && (
        <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      )}
      {showFeedback && isSelected && !isCorrect && (
        <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </button>
  );
}

/**
 * Feedback section shown after answering
 */
function FeedbackSection({ result }) {
  if (!result) return null;

  const { isCorrect, explanation } = result;

  return (
    <div
      className={`mt-4 p-4 rounded-lg ${
        isCorrect
          ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
          : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
      }`}
      data-testid="feedback-section"
    >
      <div className="flex items-center gap-2 mb-2">
        {isCorrect ? (
          <>
            <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-medium text-green-700 dark:text-green-400">Correct!</span>
          </>
        ) : (
          <>
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-medium text-red-700 dark:text-red-400">Incorrect</span>
          </>
        )}
      </div>
      {!isCorrect && explanation && (
        <p className="text-sm text-gray-700 dark:text-gray-300">{explanation}</p>
      )}
    </div>
  );
}

/**
 * Quiz results component shown after completion
 */
function QuizResults({ results, onRetry }) {
  const { score, correctCount, totalQuestions, results: questionResults } = results;
  const percentage = Math.round(score * 100);

  const getScoreColor = () => {
    if (percentage >= 80) return 'text-green-600 dark:text-green-400';
    if (percentage >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getScoreMessage = () => {
    if (percentage >= 80) return 'Excellent work! 🎉';
    if (percentage >= 60) return 'Good job! Keep practicing! 👍';
    return 'Keep learning! You\'ll get better! 💪';
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <CardTitle>Quiz Complete!</CardTitle>
        <CardDescription>{getScoreMessage()}</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Score display */}
        <div className="text-center mb-8">
          <div className={`text-6xl font-bold ${getScoreColor()}`}>
            {percentage}%
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {correctCount} out of {totalQuestions} correct
          </p>
        </div>

        {/* Results breakdown */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">Question Review</h4>
          {questionResults?.map((result, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${
                result.isCorrect
                  ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
                  : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10'
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-medium ${
                    result.isCorrect
                      ? 'bg-green-500 text-white'
                      : 'bg-red-500 text-white'
                  }`}
                >
                  {index + 1}
                </span>
                <div className="flex-1">
                  <p className="text-gray-900 dark:text-white font-medium mb-1">
                    {result.question}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Your answer: {result.options[result.userAnswer]}
                  </p>
                  {!result.isCorrect && (
                    <>
                      <p className="text-sm text-green-600 dark:text-green-400">
                        Correct answer: {result.options[result.correctAnswer]}
                      </p>
                      {result.explanation && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 italic">
                          {result.explanation}
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter className="justify-center">
        <Button onClick={onRetry} variant="outline">
          Take Another Quiz
        </Button>
      </CardFooter>
    </Card>
  );
}

export default QuizComponent;
