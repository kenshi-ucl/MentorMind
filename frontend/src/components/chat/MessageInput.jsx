import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { Button, Input } from '../ui';

export function MessageInput({ onSend, onTyping }) {
  const [message, setMessage] = useState('');
  const typingTimeoutRef = useRef(null);
  
  const handleChange = (e) => {
    setMessage(e.target.value);
    
    // Send typing indicator
    onTyping?.(true);
    
    // Clear previous timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // Stop typing indicator after 2 seconds of no input
    typingTimeoutRef.current = setTimeout(() => {
      onTyping?.(false);
    }, 2000);
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (message.trim()) {
      onSend(message.trim());
      setMessage('');
      
      // Clear typing indicator
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      onTyping?.(false);
    }
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);
  
  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <Input
        type="text"
        placeholder="Type a message..."
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        className="flex-1"
      />
      <Button type="submit" disabled={!message.trim()}>
        <Send className="w-4 h-4" />
      </Button>
    </form>
  );
}
