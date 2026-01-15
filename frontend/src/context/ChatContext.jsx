import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import websocketService from '../lib/websocket';

const ChatContext = createContext(null);

const API_BASE = 'http://localhost:5000/api';

export function ChatProvider({ children }) {
  const { token, isAuthenticated } = useAuth();
  const [directChats, setDirectChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [typingUsers, setTypingUsers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const currentChatRef = useRef(null);

  // Keep ref in sync with state
  useEffect(() => {
    currentChatRef.current = currentChat;
  }, [currentChat]);

  const fetchDirectChats = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/chat/direct`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setDirectChats(data.chats || []);
      }
    } catch (err) {
      console.error('Failed to fetch direct chats:', err);
    }
  }, [token]);

  const getOrCreateChat = async (friendId) => {
    if (!token) return null;
    
    try {
      const response = await fetch(`${API_BASE}/chat/direct/${friendId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        return data;
      }
    } catch (err) {
      console.error('Failed to get/create chat:', err);
    }
    return null;
  };

  const ensureWebSocketConnected = async () => {
    if (!websocketService.connected) {
      console.log('WebSocket not connected, connecting...');
      await websocketService.connect(token);
    }
    return websocketService.connected;
  };

  const openChat = async (chatId, chatType = 'direct') => {
    if (!token) return;
    
    setIsLoading(true);
    try {
      // Ensure websocket is connected first
      await ensureWebSocketConnected();
      
      // Fetch messages
      const response = await fetch(`${API_BASE}/chat/${chatId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      
      if (response.ok) {
        setMessages(data.messages || []);
        setCurrentChat({ id: chatId, type: chatType });
        
        // Join WebSocket room
        try {
          const joinResult = await websocketService.joinChat(chatId, chatType);
          console.log('Joined chat room:', joinResult);
        } catch (joinErr) {
          console.error('Failed to join chat room:', joinErr);
        }
      }
    } catch (err) {
      console.error('Failed to open chat:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const closeChat = async () => {
    const chat = currentChatRef.current;
    if (chat) {
      try {
        if (websocketService.connected) {
          await websocketService.leaveChat(chat.id, chat.type);
        }
      } catch (err) {
        // Ignore errors on close
      }
      setCurrentChat(null);
      setMessages([]);
      setTypingUsers({});
    }
  };

  const sendMessage = async (content) => {
    const chat = currentChatRef.current;
    
    if (!chat) {
      console.error('Cannot send message: no current chat');
      return { success: false, error: 'No chat open' };
    }
    
    if (!content || !content.trim()) {
      console.error('Cannot send message: empty content');
      return { success: false, error: 'Empty message' };
    }
    
    // Ensure websocket is connected
    try {
      await ensureWebSocketConnected();
      
      // Re-join room if needed
      if (websocketService.connected) {
        await websocketService.joinChat(chat.id, chat.type);
      }
    } catch (err) {
      console.error('Failed to ensure connection:', err);
      return { success: false, error: 'Not connected' };
    }
    
    try {
      const result = await websocketService.sendMessage(
        chat.id, 
        content.trim(), 
        chat.type
      );
      
      console.log('Send message result:', result);
      
      if (result?.success && result?.message) {
        setMessages(prev => [...prev, result.message]);
        return { success: true, message: result.message };
      }
      return { success: false, error: result?.error || 'Unknown error' };
    } catch (err) {
      console.error('Failed to send message:', err);
      return { success: false, error: err.message };
    }
  };

  const sendTypingIndicator = (isTyping) => {
    const chat = currentChatRef.current;
    if (chat && websocketService.connected) {
      websocketService.sendTyping(chat.id, isTyping, chat.type).catch(() => {});
    }
  };

  const markAsRead = async (messageIds = null) => {
    const chat = currentChatRef.current;
    if (!chat || !websocketService.connected) return;
    
    try {
      await websocketService.markAsRead(chat.id, messageIds, chat.type);
    } catch (err) {
      // Ignore errors
    }
  };

  const loadMoreMessages = async (offset) => {
    const chat = currentChatRef.current;
    if (!chat || !token) return [];
    
    try {
      const response = await fetch(
        `${API_BASE}/chat/${chat.id}/messages?offset=${offset}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const data = await response.json();
      
      if (response.ok && data.messages?.length) {
        setMessages(prev => [...data.messages, ...prev]);
        return data.messages;
      }
    } catch (err) {
      console.error('Failed to load more messages:', err);
    }
    return [];
  };

  // Handle WebSocket events
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleMessage = (message) => {
      const chat = currentChatRef.current;
      if (chat && message.chatId === chat.id) {
        setMessages(prev => [...prev, message]);
      }
      // Update chat list with new message
      setDirectChats(prev => prev.map(c => 
        c.id === message.chatId 
          ? { ...c, lastMessage: message, lastMessageAt: message.createdAt }
          : c
      ));
    };

    const handleTyping = (data) => {
      const chat = currentChatRef.current;
      if (chat && data.chatId === chat.id) {
        setTypingUsers(prev => ({
          ...prev,
          [data.userId]: data.isTyping ? data.userName : null
        }));
        
        // Clear typing indicator after 3 seconds
        if (data.isTyping) {
          setTimeout(() => {
            setTypingUsers(prev => ({
              ...prev,
              [data.userId]: null
            }));
          }, 3000);
        }
      }
    };

    const handleRead = (data) => {
      const chat = currentChatRef.current;
      if (chat && data.chatId === chat.id) {
        setMessages(prev => prev.map(msg => {
          if (data.messageIds?.includes(msg.id) || !data.messageIds) {
            const readBy = msg.readBy || [];
            if (!readBy.includes(data.userId)) {
              return { ...msg, readBy: [...readBy, data.userId] };
            }
          }
          return msg;
        }));
      }
    };

    const unsubMessage = websocketService.on('chat:message', handleMessage);
    const unsubTyping = websocketService.on('chat:typing', handleTyping);
    const unsubRead = websocketService.on('chat:read', handleRead);

    return () => {
      unsubMessage();
      unsubTyping();
      unsubRead();
    };
  }, [isAuthenticated]);

  // Fetch chats on mount
  useEffect(() => {
    if (isAuthenticated) {
      fetchDirectChats();
    }
  }, [isAuthenticated, fetchDirectChats]);

  const value = {
    directChats,
    currentChat,
    messages,
    typingUsers: Object.values(typingUsers).filter(Boolean),
    isLoading,
    getOrCreateChat,
    openChat,
    closeChat,
    sendMessage,
    sendTypingIndicator,
    markAsRead,
    loadMoreMessages,
    refreshChats: fetchDirectChats
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

export default ChatContext;
