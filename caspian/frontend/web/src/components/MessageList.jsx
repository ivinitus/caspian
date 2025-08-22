import { useRef, useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiUser, FiCpu, FiCopy, FiCheck, FiAlertTriangle } from 'react-icons/fi';
import './MessageList.css';

export function MessageList({ messages, loading, messagesEndRef, error }) {
  // Simple ref for the scroll container
  const containerRef = useRef(null);
  const loadingRef = useRef(null);
  const errorRef = useRef(null);
  const [copiedMsgIndex, setCopiedMsgIndex] = useState(null);
  
  // Auto-scroll when messages change or loading state changes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading, messagesEndRef]);
  
  // Copy message content to clipboard
  const copyToClipboard = (text, index) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedMsgIndex(index);
      setTimeout(() => setCopiedMsgIndex(null), 2000);
    });
  };
  
  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="message-list" ref={containerRef}>
      {messages.map((message, index) => (
        <div 
          key={index}
          className={`message ${message.role} message-animated`}
        >
          <div className="message-icon">
            {message.role === 'user' ? <FiUser /> : <FiCpu />}
          </div>
          <div className="message-content-wrapper">
            <div className="message-content">
              <ReactMarkdown
                components={{
                  code({node, inline, className, children, ...props}) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
            <div className="message-meta">
              {message.timestamp && (
                <span className="message-timestamp">{formatTime(message.timestamp)}</span>
              )}
              
              {message.role === 'assistant' && (
                <button 
                  className="message-copy-btn" 
                  onClick={() => copyToClipboard(message.content, index)}
                  aria-label="Copy message"
                >
                  {copiedMsgIndex === index ? <FiCheck /> : <FiCopy />}
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
      
      {loading && (
        <div 
          ref={loadingRef}
          className="message assistant typing message-animated"
        >
          <div className="message-icon">
            <FiCpu />
          </div>
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}
      
      {error && (
        <div 
          ref={errorRef}
          className="message error message-animated"
        >
          <div className="message-icon error-icon">
            <FiAlertTriangle />
          </div>
          <div className="message-content">
            <p className="error-message">{error}</p>
            <p className="error-suggestion">Please try again or refresh the page.</p>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
}
