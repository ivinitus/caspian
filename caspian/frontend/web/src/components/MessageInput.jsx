import { useState, useRef, useEffect } from 'react';
import { FiSend } from 'react-icons/fi';
import { preventFormNavigation, safeButtonClick } from '../utils/navigation';
import './MessageInput.css';

export function MessageInput({ onSendMessage, disabled, isLoading }) {
  const [input, setInput] = useState('');
  const [rows, setRows] = useState(1);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef(null);
  
  // Adjust text area height based on content
  useEffect(() => {
    if (textareaRef.current) {
      // Reset height to ensure proper calculation
      textareaRef.current.style.height = 'auto';
      
      // Calculate new height
      const scrollHeight = textareaRef.current.scrollHeight;
      const newRows = Math.min(Math.max(Math.ceil(scrollHeight / 24), 1), 5);
      
      setRows(newRows);
      textareaRef.current.style.height = `${scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    // Aggressively prevent any default behavior
    if (e) {
      e.preventDefault();
      e.stopPropagation();
      
      // Additional prevention as a safety measure
      if (e.nativeEvent) {
        e.nativeEvent.preventDefault();
        e.nativeEvent.stopPropagation();
        e.nativeEvent.stopImmediatePropagation();
      }
    }
    
    // Validate input before proceeding
    if (input && input.trim() && !disabled) {
      try {
        // Wrap in try/catch to prevent errors from bubbling up
        onSendMessage(input);
        setInput('');
        // Reset rows after sending
        setRows(1);
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
        }
      } catch (error) {
        console.error('Error in message submission:', error);
        // Don't allow the error to propagate
      }
    }
    
    // Ensure we always return false to prevent form submission
    return false;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };
  
  const placeholder = disabled 
    ? "Connecting..." 
    : "Type your message, Sir...";

  return (
    <div className={`message-input-container ${isFocused ? 'focused' : ''}`}>
      <textarea
        ref={textareaRef}
        className="message-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder={placeholder}
        disabled={disabled}
        rows={rows}
        aria-label="Message input"
      />
      
      <div className="input-actions">
        <button 
          type="button" 
          className="send-button"
          onClick={safeButtonClick(handleSubmit)}
          disabled={disabled || !input.trim()}
          aria-label="Send message"
        >
          {isLoading ? (
            <div className="button-loader" aria-hidden="true"></div>
          ) : (
            <FiSend aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  );
}
