import { useState } from 'react';
import { ChatInterface } from '../chat/ChatInterface';
import { ContentUploader } from '../content/ContentUploader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

/**
 * LessonsView - Main learning interface with chat and content upload.
 * 
 * Features:
 * - Chat with TutorAgent
 * - Upload and process content
 * - Content-aware chat responses
 * 
 * Requirements: 4.1, 4.5, 5.1, 10.3
 */
export function LessonsView() {
  const [uploadedContent, setUploadedContent] = useState([]);
  const [activeTab, setActiveTab] = useState('chat');

  const handleUploadComplete = (result) => {
    setUploadedContent((prev) => [...prev, result]);
    // Switch to chat tab after successful upload
    setActiveTab('chat');
  };

  const handleUploadError = (error) => {
    console.error('Upload error:', error);
  };

  // Get content context for chat (summaries from uploaded content)
  const contentContext = uploadedContent.flatMap((content) => content.summary || []);

  return (
    <div className="h-full flex flex-col">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
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

        <TabsContent value="chat" className="flex-1 m-0 overflow-hidden">
          <ChatInterface contentContext={contentContext} />
        </TabsContent>

        <TabsContent value="upload" className="flex-1 m-0 overflow-auto p-6">
          <div className="max-w-2xl mx-auto space-y-6">
            <ContentUploader
              onUploadComplete={handleUploadComplete}
              onError={handleUploadError}
            />

            {/* Uploaded Content List */}
            {uploadedContent.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Uploaded Content ({uploadedContent.length})
                </h3>
                <div className="space-y-3">
                  {uploadedContent.map((content, index) => (
                    <div
                      key={content.contentId || index}
                      className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
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
                            {content.filename || `Content ${index + 1}`}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {content.keyPoints?.length || 0} key points extracted
                          </p>
                        </div>
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
