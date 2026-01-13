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
   