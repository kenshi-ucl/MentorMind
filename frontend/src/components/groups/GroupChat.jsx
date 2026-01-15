import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Avatar } from '../ui/Avatar';

const API_BASE = 'http://localhost:5000/api';

export function GroupChat({ groupId }) {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchMessages();
  }, [groupId, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchMessages = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/groups/${groupId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !token) return;
    const content = input.trim();
    setInput('');
    try {
      const response = await fetch(`${API_BASE}/groups/${groupId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ content })
      });
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, data]);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };


  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <p>No messages yet</p>
            <p className="text-sm">Start the conversation!</p>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`flex gap-3 ${msg.senderId === user?.id ? 'flex-row-reverse' : ''}`}>
              <Avatar name={msg.senderName} size="sm" />
              <div className={`max-w-[70%] ${msg.senderId === user?.id ? 'text-right' : ''}`}>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{msg.senderName}</p>
                <div className={`px-4 py-2 rounded-2xl ${msg.senderId === user?.id ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'}`}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type a message..." className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-full bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
          <button type="submit" disabled={!input.trim()} className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:opacity-50">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
