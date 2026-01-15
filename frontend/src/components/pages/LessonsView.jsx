import { useState, useEffect } from 'react';
import { ChatInterface } from '../chat/ChatInterface';
import { ContentUploader } from '../content/ContentUploader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/button';

const API_BASE = 'http://localhost:5000/api';

/**
 * LessonsView - Main learning interface with chat and content upload.
 * 
 * Features:
 * - Chat with TutorAgent
 * - Upload and process content
 * - Content-aware chat responses
 * - Load existing conversations from History
 * 
 * Note: Chat history is now in a separate History page accessible from sidebar.
 * 
 * Requirements: 4.1, 4.5, 5.1, 10.3
 */
export function LessonsView({ conversationId: initialConversationId = null, onConversationChange = null }) {
  const { token } = useAuth();
  const [uploadedContent, setUploadedContent] = useState([]);
  const [contentContext, setContentContext] = useState([]);
  const [activeTab, setActiveTab] = useState('chat');
  const [reprocessingId, setReprocessingId] = useState(null);
  const [currentConversationId, setCurrentConversationId] = useState(initialConversationId);

  // Update conversation ID when prop changes (e.g., from History navigation)
  useEffect(() => {
    if (initialConversationId !== currentConversationId) {
      setCurrentConversationId(initialConversationId);
      // Switch to chat tab when loading a conversation
      if (initialConversationId) {
        setActiveTab('chat');
      }
    }
  }, [initialConversationId]);

  // Handle conversation changes from ChatInterface
  const handleConversationChange = (newConversationId) => {
    setCurrentConversationId(newConversationId);
    if (onConversationChange) {
      onConversationChange(newConversationId);
    }
  };

  // Fetch content context from backend on mount and after uploads
  const fetchContentContext = async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/content/context`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const contextStrings = data.contents.map(content => {
          const parts = [];
          parts.push(`=== Document: ${content.title || content.filename} ===`);
          if (content.summary) {
            parts.push(`Summary: ${content.summary}`);
          }
          if (content.keyPoints && content.keyPoints.length > 0) {
            parts.push(`Key Points:\n${content.keyPoints.map(p => `- ${p}`).join('\n')}`);
          }
          if (content.extractedText) {
            const maxTextLength = 10000;
            const text = content.extractedText.length > maxTextLength 
              ? content.extractedText.substring(0, maxTextLength) + '...[truncated]'
              : content.extractedText;
            parts.push(`Full Content:\n${text}`);
          }
          return parts.join('\n\n');
        });
        setContentContext(contextStrings);
        setUploadedContent(data.contents);
      }
    } catch (error) {
      console.error('Failed to fetch content context:', error);
    }
  };

  const reprocessContent = async (contentId) => {
    if (!token) return;
    
    setReprocessingId(contentId);
    try {
      const response = await fetch(`${API_BASE}/content/${contentId}/reprocess`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        await fetchContentContext();
      } else {
        const data = await response.json();
        console.error('Reprocess failed:', data.error);
      }
    } catch (error) {
      console.error('Failed to reprocess content:', error);
    } finally {
      setReprocessingId(null);
    }
  };

  useEffect(() => {
    fetchContentContext();
  }, [token]);

  const handleUploadComplete = () => {
    fetchContentContext();
    setActiveTab('chat');
  };

  const handleUploadError = (error) => {
    console.error('Upload error:', error);
  };

  return (
    <div className="h-full flex flex-col">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 min-h-0 flex flex-col">
        <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-700 px-4">
          <TabsList className="h-12">
            <TabsTrigger value="chat" className="px-4">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              Chat with Tutor
            </TabsTrigger>
            <TabsTrigger value="upload" className="px-4">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Upload Content
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="chat" className="flex-1 min-h-0 m-0 overflow-hidden">
          <ChatInterface 
            contentContext={contentContext} 
            conversationId={currentConversationId}
            onConversationChange={handleConversationChange}
          />
        </TabsContent>

        <TabsContent value="upload" className="flex-1 m-0 overflow-auto p-6">
          <div className="max-w-2xl mx-auto space-y-6">
            <ContentUploader
              onUploadComplete={handleUploadComplete}
              onError={handleUploadError}
            />

            {uploadedContent.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Uploaded Content ({uploadedContent.length})
                </h3>
                <div className="space-y-3">
                  {uploadedContent.map((content, index) => (
                    <div
                      key={content.id || index}
                      className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                          {content.fileType === 'video' ? (
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
                            {content.title || content.filename || `Content ${index + 1}`}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {content.keyPoints?.length || 0} key points extracted
                            {content.extractedText ? (
                              <span className="ml-2 text-green-600 dark:text-green-400">• Text ready for chat</span>
                            ) : (
                              <span className="ml-2 text-yellow-600 dark:text-yellow-400">• No text extracted</span>
                            )}
                          </p>
                        </div>
                        {!content.extractedText && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => reprocessContent(content.id)}
                            disabled={reprocessingId === content.id}
                          >
                            {reprocessingId === content.id ? (
                              <>
                                <svg className="w-4 h-4 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Processing...
                              </>
                            ) : (
                              'Extract Text'
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default LessonsView;
