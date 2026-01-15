import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useAuth } from '../../context/AuthContext';
import ReactMarkdown from 'react-markdown';

const API_BASE = 'http://localhost:5000/api';

/**
 * HistoryView - Displays all past chat conversations with search functionality
 */
export function HistoryView({ onNavigate }) {
  const { token } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [filteredConversations, setFilteredConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);

  // Handle continuing the conversation in Lessons
  const handleContinueChat = () => {
    if (selectedConversation && onNavigate) {
      onNavigate('/lessons', selectedConversation);
    }
  };

  // Fetch conversations on mount
  useEffect(() => {
    if (token) {
      fetchConversations();
    }
  }, [token]);

  // Filter conversations when search query changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredConversations(conversations);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = conversations.filter(conv => 
        conv.title?.toLowerCase().includes(query) ||
        conv.preview?.toLowerCase().includes(query)
      );
      setFilteredConversations(filtered);
    }
  }, [searchQuery, conversations]);

  const fetchConversations = async () => {
    if (!token) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/chat/conversations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
        setFilteredConversations(data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversation = async (conversationId) => {
    if (!token) return;
    
    setIsLoadingMessages(true);
    setSelectedConversation(conversationId);
    
    try {
      const response = await fetch(`${API_BASE}/chat/conversations/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const deleteConversation = async (e, conversationId) => {
    e.stopPropagation();
    
    if (!token) return;
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    
    try {
      const response = await fetch(`${API_BASE}/chat/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        if (selectedConversation === conversationId) {
          setSelectedConversation(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays === 1) {
      return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (diffDays < 7) {
      return date.toLocaleDateString([], { weekday: 'long', hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="h-full flex bg-gray-50 dark:bg-gray-900">
      {/* Conversations List */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col">
        {/* Header with Search */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Chat History
          </h2>
          <div className="relative">
            <svg 
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <Input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              <svg className="w-6 h-6 animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading...
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              {searchQuery ? 'No conversations found' : 'No chat history yet'}
              <p className="text-sm mt-1">
                {searchQuery ? 'Try a different search term' : 'Start chatting in Lessons to build your history'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {filteredConversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => loadConversation(conversation.id)}
                  className={`p-4 cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-700/50 ${
                    selectedConversation === conversation.id
                      ? 'bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-500'
                      : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 dark:text-white truncate">
                        {conversation.title || 'Untitled Conversation'}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {formatDate(conversation.updatedAt || conversation.createdAt)}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        {conversation.messageCount || 0} messages
                      </p>
                    </div>
                    <button
                      onClick={(e) => deleteConversation(e, conversation.id)}
                      className="p-1.5 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                      title="Delete conversation"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Conversation Detail */}
      <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 min-w-0 overflow-hidden relative">
        {selectedConversation ? (
          <>
            {/* Conversation Header */}
            <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {conversations.find(c => c.id === selectedConversation)?.title || 'Conversation'}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {formatDate(conversations.find(c => c.id === selectedConversation)?.createdAt)}
              </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-4 relative">
              {isLoadingMessages ? (
                <div className="flex items-center justify-center h-full">
                  <svg className="w-8 h-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
              ) : (
                <>
                  {messages.map((message, index) => (
                    <MessageBubble key={message.id || index} message={message} formatTime={formatTime} />
                  ))}
                  {/* Spacer for the blur overlay */}
                  <div className="h-32" />
                </>
              )}
            </div>

            {/* Blur overlay with "Continue this chat?" prompt */}
            {!isLoadingMessages && messages.length > 0 && (
              <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
                {/* Gradient blur effect */}
                <div className="h-24 bg-gradient-to-t from-white via-white/95 to-transparent dark:from-gray-900 dark:via-gray-900/95" />
                
                {/* Continue chat prompt */}
                <div className="bg-white dark:bg-gray-900 pb-6 px-6 pointer-events-auto">
                  <div className="flex flex-col items-center justify-center py-4 px-6 rounded-xl bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/30 dark:to-purple-900/30 border border-indigo-200 dark:border-indigo-700/50 shadow-lg backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <p className="text-gray-700 dark:text-gray-200 font-medium">
                        Do you want to continue this chat?
                      </p>
                    </div>
                    <Button
                      onClick={handleContinueChat}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg flex items-center gap-2"
                    >
                      <span>Yes, Continue</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <h3 className="text-lg font-medium mb-1">Select a conversation</h3>
              <p className="text-sm">Choose a conversation from the list to view its messages</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Message bubble for history view (read-only)
 */
function MessageBubble({ message, formatTime }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} w-full`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 overflow-hidden ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
        }`}
      >
        <div
          className={`text-xs font-medium mb-1 ${
            isUser ? 'text-indigo-200' : 'text-gray-500 dark:text-gray-400'
          }`}
        >
          {isUser ? 'You' : 'TutorAgent'}
        </div>

        <div className="break-words">
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <h2 className="text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white">{children}</h2>,
                  h2: ({ children }) => <h3 className="text-base font-bold mt-3 mb-2 text-gray-900 dark:text-white">{children}</h3>,
                  h3: ({ children }) => <h4 className="text-sm font-semibold mt-2 mb-1 text-gray-900 dark:text-white">{children}</h4>,
                  p: ({ children }) => <p className="mb-2 leading-relaxed text-gray-800 dark:text-gray-200">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-800 dark:text-gray-200">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-800 dark:text-gray-200">{children}</ol>,
                  li: ({ children }) => <li className="text-gray-800 dark:text-gray-200">{children}</li>,
                  strong: ({ children }) => <strong className="font-semibold text-gray-900 dark:text-white">{children}</strong>,
                  em: ({ children }) => <em className="italic text-gray-800 dark:text-gray-200">{children}</em>,
                  a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-600 dark:text-indigo-400 hover:underline">{children}</a>,
                  code: ({ inline, children }) => inline 
                    ? <code className="bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
                    : <pre className="bg-gray-800 dark:bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto my-2 border border-gray-300 dark:border-gray-600"><code className="text-sm font-mono text-gray-100">{children}</code></pre>,
                  pre: ({ children }) => <>{children}</>,
                  table: ({ children }) => (
                    <div className="my-3 overflow-x-auto">
                      <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">{children}</table>
                    </div>
                  ),
                  thead: ({ children }) => <thead className="bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100">{children}</thead>,
                  tbody: ({ children }) => <tbody className="text-gray-800 dark:text-gray-200">{children}</tbody>,
                  tr: ({ children }) => <tr className="border-b border-gray-300 dark:border-gray-600">{children}</tr>,
                  th: ({ children }) => <th className="px-3 py-2 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">{children}</th>,
                  td: ({ children }) => <td className="px-3 py-2 text-sm text-gray-800 dark:text-gray-200">{children}</td>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-indigo-500 pl-3 my-2 italic text-gray-700 dark:text-gray-300">{children}</blockquote>
                  ),
                  hr: () => <hr className="my-3 border-gray-300 dark:border-gray-600" />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className={`text-xs mt-1 ${isUser ? 'text-indigo-200' : 'text-gray-400 dark:text-gray-500'}`}>
          {formatTime(message.createdAt || message.timestamp)}
        </div>
      </div>
    </div>
  );
}

export default HistoryView;
