import { useState, useEffect, useRef } from 'react';
import { FiUser } from 'react-icons/fi';
// You can replace this SVG with a more detailed butler/Jenkins icon if desired
const ButlerIcon = () => (
  <span style={{ display: 'inline-flex', alignItems: 'center', marginRight: 8 }}>
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="16" fill="#F5F5F5" stroke="#222" strokeWidth="2"/>
      <ellipse cx="16" cy="13" rx="6" ry="7" fill="#fff" stroke="#222" strokeWidth="1.5"/>
      <ellipse cx="16" cy="13" rx="3.5" ry="4" fill="#e0e0e0"/>
      <ellipse cx="16" cy="13" rx="2.5" ry="3" fill="#fff"/>
      <ellipse cx="16" cy="13" rx="1.2" ry="1.5" fill="#222"/>
      <rect x="13" y="20" width="6" height="2.5" rx="1.2" fill="#222"/>
      <ellipse cx="16" cy="24.5" rx="2.5" ry="1.2" fill="#222"/>
    </svg>
  </span>
);
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import './Chat.css';

export function Chat() {
  const { authToken, conversationId, username } = useAuth();
  // Dynamic greeting based on time of day
  function getButlerGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning, Sir. How may I assist you today?';
    if (hour < 18) return 'Good afternoon, Sir. How may I assist you today?';
    return 'Good evening, Sir. How may I assist you today?';
  }

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: getButlerGreeting(),
      timestamp: new Date().toISOString(),
      isGreeting: true,
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 3;

  useEffect(() => {
    // Scroll to bottom whenever messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  useEffect(() => {
    // Clear error when auth token or conversation ID changes (likely reconnected)
    if (authToken && conversationId) {
      setError(null);
      reconnectAttemptsRef.current = 0;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    }
  }, [authToken, conversationId]);
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const handleSendMessage = (content) => {
    // Validate input - don't do anything if there's no content, already loading, or no connection
    if (!content || !content.trim() || loading || !conversationId || !authToken) {
      return;
    }

    try {
      // Create the user message object
      const userMsg = { 
        role: 'user', 
        content: content.trim(),
        timestamp: new Date().toISOString()
      };
      
      // Update the UI first
      setMessages(prev => [...prev, userMsg]);
      setLoading(true);
      setError(null);
      
      // Wrap API calls in a separate async function to avoid issues with async/await
      const sendMessageToAPI = async () => {
        try {
          // Save user message to conversation
          await api.sendMessage(authToken, conversationId, userMsg.content, 'user');
          
          // Get response from LLM
          const response = await api.getChatResponse(authToken, [...messages, userMsg]);
          
          // Check if response has the expected format
          if (!response || typeof response !== 'object') {
            throw new Error('Invalid response from server');
          }
          
          // Get the reply text, with fallbacks for different API formats
          let reply = response.text || response.content || response.message || '';
          
          // Handle empty responses
          if (!reply || reply.trim() === '') {
            reply = 'Sorry Sir, I could not generate a proper response. Please try again.';
          }
          
          // Create assistant message
          const assistantMsg = { 
            role: 'assistant', 
            content: reply,
            timestamp: new Date().toISOString()
          };
          
          // Update UI with the assistant's response
          setMessages(prev => [...prev, assistantMsg]);
          
          // Save assistant message to conversation
          await api.sendMessage(authToken, conversationId, assistantMsg.content, 'assistant');
          
          // Reset reconnect attempts on successful communication
          reconnectAttemptsRef.current = 0;
        } catch (error) {
          console.error('Error in chat communication:', error);
          
          // Handle specific error types
          if (error.message.includes('expired') || error.message.includes('401')) {
            setError('Your session has expired. Please log in again.');
          } else if (error.message.includes('network') || error.message.includes('Failed to fetch')) {
            setError('Network connection lost. Attempting to reconnect...');
            attemptReconnect();
          } else {
            setError(`Communication error: ${error.message}`);
          }
        } finally {
          // Always set loading to false
          setLoading(false);
        }
      };
      
      // Call the API function but don't await it directly
      sendMessageToAPI().catch(err => {
        console.error("Unhandled promise rejection:", err);
        setLoading(false);
        setError("An unexpected error occurred. Please try again.");
      });
    } catch (outerError) {
      // Catch any errors in the outer function to prevent page blanking
      console.error("Critical error in handleSendMessage:", outerError);
      setLoading(false);
      setError("A critical error occurred. Please refresh the page and try again.");
    }
  };
  
  const attemptReconnect = () => {
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      setError('Unable to reconnect after multiple attempts. Please refresh the page.');
      return;
    }
    
    reconnectAttemptsRef.current += 1;
    
    // Exponential backoff: 2s, 4s, 8s, etc.
    const backoffTime = 2000 * Math.pow(2, reconnectAttemptsRef.current - 1);
    
    reconnectTimeoutRef.current = setTimeout(async () => {
      try {
        setError(`Attempting to reconnect (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`);
        
        // Try to get a new token and conversation
        const token = await api.authenticate(username);
        const conversation = await api.startConversation(token, username);
        
        // Update these via context/state management (ideally handled in AuthContext)
        // For now, we'll just show a message prompting refresh
        setError('Reconnected! Please refresh the page to continue.');
      } catch (error) {
        console.error('Reconnection failed:', error);
        setError('Reconnection failed. Trying again...');
        attemptReconnect();
      }
    }, backoffTime);
  };

  return (
    <div className="chat">
      {/* Fallback UI - show error message with retry button if there's an error */}
      {error && (
        <div className="chat-error">
          <div className="error-message">
            <p>{error}</p>
            <button 
              type="button" 
              className="retry-button"
              onClick={() => setError(null)}
            >
              Retry
            </button>
          </div>
        </div>
      )}



      <MessageList 
        messages={messages} 
        loading={loading} 
        messagesEndRef={messagesEndRef}
        error={error}
      />

      <div className="chat-input-area">
        <MessageInput 
          onSendMessage={handleSendMessage} 
          disabled={loading || !conversationId || !authToken || !!error}
          isLoading={loading}
        />

  {/* Loading indicator removed as per user request */}
      </div>
    </div>
  );
}
