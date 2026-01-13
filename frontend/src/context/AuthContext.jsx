import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_BASE = 'http://localhost:5000/api';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing session on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('mentormind_token');
    const storedUser = localStorage.getItem('mentormind_user');
    const storedIsAnonymous = localStorage.getItem('mentormind_anonymous');
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
      setIsAnonymous(storedIsAnonymous === 'true');
    }
    setIsLoading(false);
  }, []);

  const saveSession = (userData, sessionToken, anonymous = false) => {
    localStorage.setItem('mentormind_token', sessionToken);
    localStorage.setItem('mentormind_user', JSON.stringify(userData));
    localStorage.setItem('mentormind_anonymous', String(anonymous));
    setToken(sessionToken);
    setUser(userData);
    setIsAnonymous(anonymous);
  };

  const clearSession = () => {
    localStorage.removeItem('mentormind_token');
    localStorage.removeItem('mentormind_user');
    localStorage.removeItem('mentormind_anonymous');
    setToken(null);
    setUser(null);
    setIsAnonymous(false);
  };

  const register = async (email, password, name) => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name })
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }
      
      saveSession(data.user, data.token, false);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const login = async (email, password) => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }
      
      saveSession(data.user, data.token, false);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const continueAnonymously = async () => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/auth/anonymous`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to create anonymous session');
      }
      
      saveSession(data.user, data.sessionId, true);
      return { success: true };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
      } catch (err) {
        // Ignore logout errors, clear session anyway
      }
    }
    clearSession();
  };

  const value = {
    user,
    token,
    isAnonymous,
    isLoading,
    isAuthenticated: !!user,
    error,
    register,
    login,
    continueAnonymously,
    logout,
    clearError: () => setError(null)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
