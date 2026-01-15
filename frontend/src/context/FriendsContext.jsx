import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import websocketService from '../lib/websocket';

const FriendsContext = createContext(null);

const API_BASE = 'http://localhost:5000/api';

export function FriendsProvider({ children }) {
  const { token, isAuthenticated } = useAuth();
  const [friends, setFriends] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [sentRequests, setSentRequests] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchFriends = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/friends`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setFriends(data.friends || []);
      }
    } catch (err) {
      console.error('Failed to fetch friends:', err);
    }
  }, [token]);

  const fetchPendingRequests = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/friends/requests?type=received`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setPendingRequests(data.requests || []);
      }
    } catch (err) {
      console.error('Failed to fetch pending requests:', err);
    }
  }, [token]);

  const fetchSentRequests = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE}/friends/requests?type=sent`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setSentRequests(data.requests || []);
      }
    } catch (err) {
      console.error('Failed to fetch sent requests:', err);
    }
  }, [token]);

  const searchUsers = async (query) => {
    if (!token || query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/friends/search?q=${encodeURIComponent(query)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      if (response.ok) {
        setSearchResults(data.users || []);
      }
    } catch (err) {
      console.error('Failed to search users:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const sendFriendRequest = async (recipientId) => {
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
      const response = await fetch(`${API_BASE}/friends/request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ recipientId })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { success: false, error: data.error };
      }
      
      await fetchSentRequests();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const acceptRequest = async (requestId) => {
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
      const response = await fetch(`${API_BASE}/friends/requests/${requestId}/accept`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const data = await response.json();
        return { success: false, error: data.error };
      }
      
      await Promise.all([fetchFriends(), fetchPendingRequests()]);
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const declineRequest = async (requestId) => {
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
      const response = await fetch(`${API_BASE}/friends/requests/${requestId}/decline`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const data = await response.json();
        return { success: false, error: data.error };
      }
      
      await fetchPendingRequests();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const removeFriend = async (friendId) => {
    if (!token) return { success: false, error: 'Not authenticated' };
    
    try {
      const response = await fetch(`${API_BASE}/friends/${friendId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const data = await response.json();
        return { success: false, error: data.error };
      }
      
      await fetchFriends();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  // Handle presence updates from WebSocket
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleOnline = (data) => {
      setFriends(prev => prev.map(friend => 
        friend.id === data.userId 
          ? { ...friend, isOnline: true, status: 'available' }
          : friend
      ));
    };

    const handleOffline = (data) => {
      setFriends(prev => prev.map(friend => 
        friend.id === data.userId 
          ? { ...friend, isOnline: false, lastSeen: data.lastSeen }
          : friend
      ));
    };

    const handleStatus = (data) => {
      setFriends(prev => prev.map(friend => 
        friend.id === data.userId 
          ? { ...friend, status: data.status }
          : friend
      ));
    };

    const unsubOnline = websocketService.on('presence:online', handleOnline);
    const unsubOffline = websocketService.on('presence:offline', handleOffline);
    const unsubStatus = websocketService.on('presence:status', handleStatus);

    return () => {
      unsubOnline();
      unsubOffline();
      unsubStatus();
    };
  }, [isAuthenticated]);

  // Fetch data on mount
  useEffect(() => {
    if (isAuthenticated) {
      fetchFriends();
      fetchPendingRequests();
      fetchSentRequests();
    }
  }, [isAuthenticated, fetchFriends, fetchPendingRequests, fetchSentRequests]);

  const value = {
    friends,
    pendingRequests,
    sentRequests,
    searchResults,
    isLoading,
    error,
    pendingCount: pendingRequests.length,
    searchUsers,
    sendFriendRequest,
    acceptRequest,
    declineRequest,
    removeFriend,
    refreshFriends: fetchFriends,
    refreshRequests: fetchPendingRequests,
    clearSearch: () => setSearchResults([]),
    clearError: () => setError(null)
  };

  return (
    <FriendsContext.Provider value={value}>
      {children}
    </FriendsContext.Provider>
  );
}

export function useFriends() {
  const context = useContext(FriendsContext);
  if (!context) {
    throw new Error('useFriends must be used within a FriendsProvider');
  }
  return context;
}

export default FriendsContext;
