import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Avatar } from '../ui/Avatar';

const API_BASE = 'http://localhost:5000/api';

export function GroupInvite({ groupId, onClose, onInvited }) {
  const { token } = useAuth();
  const [friends, setFriends] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchFriends();
  }, []);

  const fetchFriends = async () => {
    try {
      const response = await fetch(`${API_BASE}/friends`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setFriends(data.friends || []);
      }
    } catch (err) {
      console.error('Failed to fetch friends:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (friendId) => {
    setSelected(prev =>
      prev.includes(friendId)
        ? prev.filter(id => id !== friendId)
        : [...prev, friendId]
    );
  };

  const handleInvite = async () => {
    if (selected.length === 0) return;

    setSending(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/groups/${groupId}/invite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ userIds: selected })
      });

      const data = await response.json();

      if (response.ok) {
        onInvited(data.successful || []);
        onClose();
      } else {
        setError(data.error || 'Failed to send invites');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full max-h-[80vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Invite Friends</h3>
          <button
            onClick={onClose}
            className="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
            </div>
          ) : friends.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <p>No friends to invite</p>
              <p className="text-sm mt-1">Add friends first to invite them to groups</p>
            </div>
          ) : (
            <div className="space-y-2">
              {friends.map(friend => (
                <button
                  key={friend.id}
                  onClick={() => toggleSelect(friend.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    selected.includes(friend.id)
                      ? 'bg-indigo-50 dark:bg-indigo-900/20 border-2 border-indigo-500'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700 border-2 border-transparent'
                  }`}
                >
                  <Avatar name={friend.name} size="sm" />
                  <span className="flex-1 text-left text-gray-900 dark:text-white">
                    {friend.name}
                  </span>
                  {selected.includes(friend.id) && (
                    <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            onClick={handleInvite}
            disabled={sending || selected.length === 0}
            className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sending ? 'Sending...' : `Invite (${selected.length})`}
          </button>
        </div>
      </div>
    </div>
  );
}
