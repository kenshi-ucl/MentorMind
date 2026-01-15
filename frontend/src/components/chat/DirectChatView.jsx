import { useEffect, useRef } from 'react';
import { ArrowLeft, Phone, Video } from 'lucide-react';
import { useChat } from '../../context/ChatContext';
import { Button } from '../ui';
import { Avatar } from '../ui/Avatar';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import audioService from '../../lib/audio';

export function DirectChatView({ friend, onClose, onVoiceCall, onVideoCall }) {
  const { messages, typingUsers, sendMessage, sendTypingIndicator, markAsRead, closeChat } = useChat();
  const messagesEndRef = useRef(null);
  
  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Mark messages as read when viewing
  useEffect(() => {
    if (messages.length > 0) {
      markAsRead();
    }
  }, [messages.length]);
  
  const handleClose = () => {
    closeChat();
    onClose();
  };
  
  const handleSend = async (content) => {
    if (!content.trim()) return;
    
    const result = await sendMessage(content);
    console.log('Send result:', result);
    if (result.success) {
      sendTypingIndicator(false);
    } else {
      console.error('Failed to send message:', result.error);
      // Could show a toast notification here
    }
  };
  
  const handleTyping = (isTyping) => {
    sendTypingIndicator(isTyping);
  };
  
  const handleVoiceCall = async () => {
    // Initialize audio on user interaction
    await audioService.init();
    onVoiceCall?.();
  };
  
  const handleVideoCall = async () => {
    // Initialize audio on user interaction
    await audioService.init();
    onVideoCall?.();
  };
  
  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={handleClose}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <Avatar name={friend.name} isOnline={friend.isOnline} showStatus />
          <div>
            <p className="font-medium text-gray-900 dark:text-white">
              {friend.name}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {friend.isOnline ? 'Online' : 'Offline'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={handleVoiceCall}>
            <Phone className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleVideoCall}>
            <Video className="w-5 h-5" />
          </Button>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      
      {/* Typing indicator */}
      {typingUsers.length > 0 && (
        <div className="px-4 pb-2">
          <TypingIndicator users={typingUsers} />
        </div>
      )}
      
      {/* Input */}
      <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <MessageInput onSend={handleSend} onTyping={handleTyping} />
      </div>
    </div>
  );
}
