import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useAuth } from '../../context/AuthContext';

const API_BASE = 'http://localhost:5000/api';

/**
 * ChatInterface component for TutorAgent interaction.
 * Displays conversation history and allows users to send messages.
 * Supports both streaming and non-streaming responses.
 * 
 * Requirements: 4.1, 4.3, 4.6, 2.5
 */
export function ChatInterface({ 
  contentContext = [], 
  enableStreaming = true,
  conversationId: initialConversationId = null,
  onConversationChange = null
}) {
  const { token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(initialConversationId);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Load conversation when conversationId changes
  useEffect(() => {
    if (initialConversationId !== conversationId) {
      setConversationId(initialConversationId);
    }
  }, [initialConversationId]);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId && token) {
      loadConversation(conversationId);
    } else if (!conversationId) {
      setMessages([]);
    }
  }, [conversationId, token]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Load a conversation's messages from the backend
   */
  const loadConversation = async (convId) => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/chat/conversations/${convId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const loadedMessages = (data.messages || []).map(msg => ({
          id: msg.messageId || `msg-${msg.id}`,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.createdAt || msg.timestamp)
        }));
        setMessages(loadedMessages);
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  /**
   * Send a message to the TutorAgent API with streaming support
   */
  const sendMessage = async (content) => {
    if (!content.trim()) return;

    // Cancel any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    // Add user message to conversation
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    // Create placeholder for assistant message (for streaming)
    const assistantMessageId = `assistant-${Date.now()}`;
    
    if (enableStreaming) {
      await sendStreamingMessage(content.trim(), assistantMessageId);
    } else {
      await sendNonStreamingMessage(content.trim(), assistantMessageId);
    }
  };

  /**
   * Send message with streaming response (SSE)
   */
  const sendStreamingMessage = async (content, assistantMessageId) => {
    try {
      setIsStreaming(true);
      
      // Add empty assistant message that will be updated with streamed content
      const assistantMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: content,
          conversationId: conversationId,
          contentContext: contentContext,
          stream: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to send message');
      }

      // Process SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            continue;
          }
          
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            try {
              // Try to parse as JSON first (for done/error events)
              const parsed = JSON.parse(data);
              
              if (parsed.error) {
                throw new Error(parsed.error);
              }
              
              if (parsed.messageId) {
                // Done event - update conversation ID if new
                if (parsed.conversationId && !conversationId) {
                  setConversationId(parsed.conversationId);
                  if (onConversationChange) {
                    onConversationChange(parsed.conversationId);
                  }
                }
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMessageId
                      ? { ...m, isStreaming: false }
                      : m
                  )
                );
              }
            } catch (parseError) {
              // Not JSON, treat as text chunk
              const chunk = data
                .replace(/\\n/g, '\n')
                .replace(/\\r/g, '\r')
                .replace(/\\"/g, '"')
                .replace(/\\\\/g, '\\');
              
              fullContent += chunk;
              
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMessageId
                    ? { ...m, content: fullContent }
                    : m
                )
              );
            }
          }
        }
      }

      // Ensure streaming flag is removed
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessageId
            ? { ...m, isStreaming: false }
            : m
        )
      );

    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      
      setError(err.message || 'Failed to send message. Please try again.');
      setMessages((prev) => prev.filter((m) => m.id !== assistantMessageId));
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      inputRef.current?.focus();
    }
  };

  /**
   * Send message with non-streaming response
   */
  const sendNonStreamingMessage = async (content, assistantMessageId) => {
    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: content,
          conversationId: conversationId,
          contentContext: contentContext,
          stream: false,
        }),
        signal: abortControllerRef.current.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to send message');
      }

      // Update conversation ID if new
      if (data.conversationId && !conversationId) {
        setConversationId(data.conversationId);
        if (onConversationChange) {
          onConversationChange(data.conversationId);
        }
      }

      // Add assistant response to conversation
      const assistantMessage = {
        id: data.messageId || assistantMessageId,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setError(err.message || 'Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isLoading && inputValue.trim()) {
      sendMessage(inputValue);
    }
  };

  /**
   * Handle key press (Enter to send)
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  /**
   * Format timestamp for display
   */
  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Chat Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Chat with TutorAgent
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Ask questions and get explanations
        </p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 mb-4 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-indigo-600 dark:text-indigo-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Start a conversation
            </h3>
            <p className="text-gray-500 dark:text-gray-400 max-w-sm">
              Ask me anything about your studies. I'm here to help you learn and understand concepts better.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            formatTime={formatTime}
          />
        ))}

        {isLoading && !isStreaming && <LoadingIndicator />}

        {error && (
          <div className="flex justify-center">
            <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question..."
            disabled={isLoading}
            className="flex-1"
            aria-label="Message input"
          />
          <Button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            aria-label="Send message"
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}


/**
 * Individual message bubble component
 */
function MessageBubble({ message, formatTime }) {
  const isUser = message.role === 'user';
  const isStreaming = message.isStreaming;

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      data-testid={`message-${message.role}`}
    >
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
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
          {isStreaming && (
            <span className="ml-2 inline-flex items-center">
              <span className="animate-pulse">typing</span>
              <span className="ml-1 flex space-x-0.5">
                <span className="w-1 h-1 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1 h-1 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1 h-1 bg-indigo-500 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </span>
          )}
        </div>

        <div className="break-words">
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h2 className="text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white border-b border-gray-300 dark:border-gray-600 pb-1">{children}</h2>
                  ),
                  h2: ({ children }) => (
                    <h3 className="text-base font-bold mt-3 mb-2 text-gray-900 dark:text-white">{children}</h3>
                  ),
                  h3: ({ children }) => (
                    <h4 className="text-sm font-semibold mt-2 mb-1 text-gray-900 dark:text-white">{children}</h4>
                  ),
                  p: ({ children }) => (
                    <p className="mb-2 text-gray-800 dark:text-gray-200 leading-relaxed">{children}</p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-inside mb-2 space-y-1 text-gray-800 dark:text-gray-200">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-inside mb-2 space-y-1 text-gray-800 dark:text-gray-200">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-gray-800 dark:text-gray-200">{children}</li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-gray-900 dark:text-white">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic text-gray-800 dark:text-gray-200">{children}</em>
                  ),
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-600 dark:text-indigo-400 hover:underline">{children}</a>
                  ),
                  code: ({ inline, children }) => {
                    if (inline) {
                      return <code className="bg-gray-300 dark:bg-gray-600 text-gray-900 dark:text-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>;
                    }
                    return (
                      <pre className="bg-gray-800 dark:bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto my-2 border border-gray-300 dark:border-gray-600">
                        <code className="text-sm font-mono text-gray-100">{children}</code>
                      </pre>
                    );
                  },
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
          {isStreaming && !message.content && (
            <span className="text-gray-400 dark:text-gray-500 italic">Thinking...</span>
          )}
        </div>

        {!isStreaming && (
          <div className={`text-xs mt-1 ${isUser ? 'text-indigo-200' : 'text-gray-400 dark:text-gray-500'}`}>
            {formatTime(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Loading indicator component
 */
function LoadingIndicator() {
  return (
    <div className="flex justify-start" data-testid="loading-indicator">
      <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-sm text-gray-500 dark:text-gray-400">TutorAgent is thinking...</span>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
