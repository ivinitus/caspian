import { createContext, useState, useEffect, useContext, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

// Local storage keys
const TOKEN_KEY = 'caspian_auth_token';
const CONVERSATION_KEY = 'caspian_conversation_id';
const TOKEN_TIMESTAMP_KEY = 'caspian_token_timestamp';

// Token expiration time (24 hours)
const TOKEN_EXPIRATION_MS = 24 * 60 * 60 * 1000;

// Fixed username for sole user
const FIXED_USERNAME = 'sir';

export function AuthProvider({ children }) {
  const [authToken, setAuthToken] = useState(() => {
    return localStorage.getItem(TOKEN_KEY) || null;
  });
  const [conversationId, setConversationId] = useState(() => {
    return localStorage.getItem(CONVERSATION_KEY) || null;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authStatus, setAuthStatus] = useState('checking'); // 'checking', 'authenticated', 'unauthenticated', 'expired'

  // Check if token is expired
  const isTokenExpired = useCallback(() => {
    const tokenTimestamp = localStorage.getItem(TOKEN_TIMESTAMP_KEY);
    if (!tokenTimestamp) return true;
    
    const elapsed = Date.now() - parseInt(tokenTimestamp, 10);
    return elapsed > TOKEN_EXPIRATION_MS;
  }, []);

  // Function to logout
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(CONVERSATION_KEY);
    localStorage.removeItem(TOKEN_TIMESTAMP_KEY);
    setAuthToken(null);
    setConversationId(null);
    setAuthStatus('unauthenticated');
  }, []);

  // Function to authenticate
  const login = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setAuthStatus('checking');
      
      // Get auth token
      const token = await api.authenticate(FIXED_USERNAME);
      setAuthToken(token);
      localStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(TOKEN_TIMESTAMP_KEY, Date.now().toString());
      
      // Start conversation
      const conversation = await api.startConversation(token, FIXED_USERNAME);
      setConversationId(conversation.id);
      localStorage.setItem(CONVERSATION_KEY, conversation.id);
      
      setAuthStatus('authenticated');
      return { token, conversationId: conversation.id };
    } catch (err) {
      console.error("Authentication failed:", err);
      setError(err.message);
      setAuthStatus('unauthenticated');
      logout(); // Clear any partial state
      throw err;
    } finally {
      setLoading(false);
    }
  }, [logout]);
  
  // Function to refresh the token
  const refreshSession = useCallback(async () => {
    try {
      return await login();
    } catch (err) {
      console.error("Session refresh failed:", err);
      throw err;
    }
  }, [login]);

  // Initialize authentication
  useEffect(() => {
    async function initializeAuth() {
      try {
        setLoading(true);
        setError(null);
        
        // Check if we have a token and conversation
        if (authToken && conversationId) {
          // Check if token is expired
          if (isTokenExpired()) {
            setAuthStatus('expired');
            await refreshSession();
            return;
          }
          
          // Token is valid
          setAuthStatus('authenticated');
          return;
        }
        
        // No token or conversation, start fresh
        await login();
      } catch (err) {
        console.error("Authentication initialization failed:", err);
        setError(err.message);
        setAuthStatus('unauthenticated');
      } finally {
        setLoading(false);
      }
    }
    
    initializeAuth();
  }, [authToken, conversationId, isTokenExpired, login, refreshSession]);

  const value = {
    authToken,
    conversationId,
    username: FIXED_USERNAME,
    loading,
    error,
    authStatus,
    isAuthenticated: authStatus === 'authenticated',
    logout,
    login,
    refreshSession
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
