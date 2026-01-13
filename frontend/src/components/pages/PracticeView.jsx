import { useState, useEffect } from 'react';
import { QuizComponent } from '../quiz/QuizComponent';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useAuth } from '../../context/AuthContext';

const API_BASE = 'http://localhost:5000/api';

/**
 * PracticeView - Quiz practice interface.
 * 
 * Features:
 * - Topic selection for quiz generation
 * - Quiz taking interface
 * - Content-based quiz option
 * 
 * Requirements: 6.1, 6.2, 10.3
 */
export function PracticeView() {
  const { token } = useAuth();
  const [mode, setMode] = useState('select'); // 'select' | 'quiz'
  const [selectedTopic, setSelectedTopic] = useState('');
  const [customTopic, setCustomTopic] = useState('');
  const [contentList, setContentList] = useState([]);
  const [selectedContentId, setSelectedContentId] = useState(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);

  // Predefined topics for quick selection
  const suggestedTopics = [
    'Mathematics',
    'Science',
    'History',
    'Programming',
    'Literature',
    'Geography',
  ];

  // Fetch uploaded content for content-based quizzes
  useEffect(() => {
    fetchContent();
  }, [token]);

  const fetchContent = async () => {
    setIsLoadingContent(true);
    try {
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/content/list`, {
        method: 'GET',
        headers,
      });
      if (response.ok) {
        const data = await response.json();
        setContentList(data.contents || []);
      }
    } catch (err) {
      console.error('Failed to fetch content:', err);
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleTopicSelect = (topic) => {
    setSelectedTopic(topic);
    setSelectedContentId(null);
  };

  const handleContentSelect = (contentId) => {
    setSelectedContentId(contentId);
    setSelectedTopic('');
    setCustomTopic('');
  };

  const handleStartQuiz = () => {
    const topic = customTopic.trim() || selectedTopic;
    if (topic || selectedContentId) {
      setMode('quiz');
    }
  };

  const handleQuizComplete = (results) => {
    console.log('Quiz completed:', results);
  };

  const handleBackToSelect = () => {
    setMode('select');
    setSelectedTopic('');
    setCustomTopic('');
    setSelectedContentId(null);
  };

  // Quiz mode - show the quiz component
  if (mode === 'quiz') {
    const topic = customTopic.trim() || selectedTopic;
    return (
      <div className="p-6 overflow-auto h-full">
        <div className="mb-4">
          <Button variant="ghost" onClick={handleBackToSelect} className="gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Topic Selection
          </Button>
        </div>
        <QuizComponent
          topic={topic || null}
          contentId={selectedContentId}
          questionCount={5}
          onComplete={handleQuizComplete}
        />
      </div>
    );
  }

  // Select mode - show topic/content selection
  return (
    <div className="p-6 overflow-auto h-full">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Practice</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Test your knowledge with AI-generated quizzes
          </p>
        </div>

        {/* Topic Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Choose a Topic</CardTitle>
            <CardDescription>
              Select a suggested topic or enter your own
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Suggested Topics */}
            <div className="flex flex-wrap gap-2">
              {suggestedTopics.map((topic) => (
                <Button
                  key={topic}
                  variant={selectedTopic === topic ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleTopicSelect(topic)}
                >
                  {topic}
                </Button>
              ))}
            </div>

            {/* Custom Topic Input */}
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Or enter a custom topic..."
                value={customTopic}
                onChange={(e) => {
                  setCustomTopic(e.target.value);
                  setSelectedTopic('');
                  setSelectedContentId(null);
                }}
                className="flex-1"
              />
            </div>
          </CardContent>
        </Card>

        {/* Content-Based Quiz Option */}
        {contentList.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Quiz from Uploaded Content</CardTitle>
              <CardDescription>
                Generate a quiz based on your uploaded materials
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingContent ? (
                <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                  Loading content...
                </div>
              ) : (
                <div className="space-y-2">
                  {contentList.map((content) => (
                    <button
                      key={content.id}
                      onClick={() => handleContentSelect(content.id)}
                      className={`w-full p-3 rounded-lg border-2 transition-colors text-left flex items-center gap-3 ${
                        selectedContentId === content.id
                          ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700'
                      }`}
                    >
                      <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800">
                        {content.type === 'video' ? (
                          <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 dark:text-white">
                          {content.filename}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {content.keyPoints?.length || 0} key points
                        </p>
                      </div>
                      {selectedContentId === content.id && (
                        <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Start Quiz Button */}
        <div className="flex justify-center">
          <Button
            size="lg"
            onClick={handleStartQuiz}
            disabled={!selectedTopic && !customTopic.trim() && !selectedContentId}
            className="px-8"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Start Quiz
          </Button>
        </div>
      </div>
    </div>
  );
}

export default PracticeView;
