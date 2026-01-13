import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { useAuth } from '../../context/AuthContext';

const API_BASE = 'http://localhost:5000/api';

/**
 * ProgressDashboard component for visualizing user learning progress.
 * 
 * Features:
 * - Display success rate statistics
 * - Display topics mastered and needing improvement
 * - Render progress over time chart
 * 
 * Requirements: 7.1, 7.2, 7.3, 7.4
 */
export function ProgressDashboard() {
  const { token } = useAuth();
  const [progressData, setProgressData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch progress data from the API
   */
  const fetchProgress = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/progress`, {
        method: 'GET',
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch progress');
      }

      setProgressData(data.progressData);
    } catch (err) {
      setError(err.message || 'Failed to load progress data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProgress();
  }, [token]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
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
          <p className="text-gray-600 dark:text-gray-400">Loading progress...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardContent className="py-12 text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
          <Button onClick={fetchProgress} variant="outline">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  // No progress data yet
  if (!progressData || progressData.totalQuizzes === 0) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>Your Progress</CardTitle>
          <CardDescription>Track your learning journey</CardDescription>
        </CardHeader>
        <CardContent className="py-12 text-center">
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
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No Progress Yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Complete some quizzes to start tracking your progress!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Your Progress</h1>
          <p className="text-gray-600 dark:text-gray-400">Track your learning journey</p>
        </div>
        <Button onClick={fetchProgress} variant="outline" size="sm">
          Refresh
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Success Rate"
          value={`${progressData.successRate}%`}
          description={`${progressData.correctAnswers} of ${progressData.totalQuestions} correct`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color={progressData.successRate >= 80 ? 'green' : progressData.successRate >= 50 ? 'yellow' : 'red'}
        />
        <StatCard
          title="Quizzes Completed"
          value={progressData.totalQuizzes}
          description="Total quizzes taken"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
          color="indigo"
        />
        <StatCard
          title="Topics Mastered"
          value={progressData.topicsMastered?.length || 0}
          description="Topics with ≥80% success"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          }
          color="cyan"
        />
      </div>

      {/* Topics Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Topics Mastered */}
        <TopicsList
          title="Topics Mastered"
          topics={progressData.topicsMastered || []}
          emptyMessage="Keep practicing to master topics!"
          type="mastered"
        />

        {/* Topics Needing Work */}
        <TopicsList
          title="Topics to Improve"
          topics={progressData.topicsNeedingWork || []}
          emptyMessage="Great job! No topics need extra attention."
          type="needs_work"
        />
      </div>

      {/* Progress Over Time Chart */}
      <ProgressChart history={progressData.progressOverTime || []} />
    </div>
  );
}

/**
 * Stat card component for displaying a single metric
 */
function StatCard({ title, value, description, icon, color }) {
  const colorClasses = {
    green: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
    yellow: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400',
    red: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    indigo: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400',
    cyan: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400',
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Topics list component
 */
function TopicsList({ title, topics, emptyMessage, type }) {
  const iconColor = type === 'mastered' 
    ? 'text-green-500' 
    : 'text-orange-500';
  
  const bgColor = type === 'mastered'
    ? 'bg-green-50 dark:bg-green-900/20'
    : 'bg-orange-50 dark:bg-orange-900/20';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {topics.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm italic">
            {emptyMessage}
          </p>
        ) : (
          <ul className="space-y-2">
            {topics.map((topic, index) => (
              <li
                key={index}
                className={`flex items-center gap-2 p-2 rounded-lg ${bgColor}`}
              >
                {type === 'mastered' ? (
                  <svg className={`w-5 h-5 ${iconColor}`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className={`w-5 h-5 ${iconColor}`} fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                )}
                <span className="text-gray-700 dark:text-gray-300">{topic}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Simple progress chart component
 */
function ProgressChart({ history }) {
  if (!history || history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Progress Over Time</CardTitle>
          <CardDescription>Your quiz scores over time</CardDescription>
        </CardHeader>
        <CardContent className="py-8 text-center">
          <p className="text-gray-500 dark:text-gray-400 text-sm italic">
            Complete more quizzes to see your progress chart!
          </p>
        </CardContent>
      </Card>
    );
  }

  // Get the last 10 entries for display
  const recentHistory = history.slice(-10);
  const maxScore = 100;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Progress Over Time</CardTitle>
        <CardDescription>Your recent quiz scores</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-48 flex items-end gap-2">
          {recentHistory.map((entry, index) => {
            const height = (entry.score / maxScore) * 100;
            const barColor = entry.score >= 80 
              ? 'bg-green-500' 
              : entry.score >= 50 
                ? 'bg-yellow-500' 
                : 'bg-red-500';
            
            return (
              <div
                key={index}
                className="flex-1 flex flex-col items-center gap-1"
              >
                <div className="w-full flex flex-col items-center justify-end h-40">
                  <span className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                    {Math.round(entry.score)}%
                  </span>
                  <div
                    className={`w-full rounded-t-md ${barColor} transition-all duration-300`}
                    style={{ height: `${height}%`, minHeight: '4px' }}
                    title={`${entry.topic || 'Quiz'}: ${Math.round(entry.score)}%`}
                  />
                </div>
                <span className="text-xs text-gray-400 truncate max-w-full" title={entry.topic}>
                  {entry.topic ? entry.topic.substring(0, 8) : `Q${index + 1}`}
                </span>
              </div>
            );
          })}
        </div>
        
        {/* Legend */}
        <div className="flex justify-center gap-4 mt-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-500" />
            <span className="text-gray-500 dark:text-gray-400">≥80%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-yellow-500" />
            <span className="text-gray-500 dark:text-gray-400">50-79%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span className="text-gray-500 dark:text-gray-400">&lt;50%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ProgressDashboard;
