import { useState, useEffect, useRef } from 'react';
import './App.css';

const API_URL = '/api';

function FileUpload({ authToken }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file || !authToken) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/rag/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Successfully uploaded ${data.filename}`);
      } else {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
      }
    } catch (e) {
      setMessage(e.message);
    }
    setUploading(false);
  };

  return (
    <div className="file-upload">
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || uploading || !authToken}>
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
      {message && <p>{message}</p>}
    </div>
  );
}


function App() {
  const [authToken, setAuthToken] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello Sir, I am Caspian. How may I assist you today?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const loginAndStart = async () => {
      try {
        // Step 1: Fetch the auth token
        const tokenRes = await fetch(`${API_URL}/auth/token/from-username`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'sir' }),
        });
        if (!tokenRes.ok) throw new Error('Failed to get auth token');
        const tokenData = await tokenRes.json();
        const token = tokenData.access_token;
        setAuthToken(token);

        // Step 2: Start a new conversation using the token
        const convRes = await fetch(`${API_URL}/conversations/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ username: 'sir' }),
        });
        if (!convRes.ok) throw new Error('Failed to start conversation');
        const convData = await convRes.json();
        setConversationId(convData.id);

      } catch (e) {
        console.error("Initialization failed:", e);
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry Sir, I could not connect to the server.' }]);
      }
    };
    loginAndStart();
  }, []);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !conversationId || !authToken) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ content: userMsg.content, sender: 'user' }),
      });

      const res = await fetch(`${API_URL}/llm/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ messages: [...messages, userMsg].map(({role, content}) => ({role, content})) }),
      });

      if (res.ok) {
        const data = await res.json();
        const reply = data.text || 'Sorry Sir, I could not process that.';
        const assistantMsg = { role: 'assistant', content: reply };
        
        setMessages(prev => [...prev, assistantMsg]);

        await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({ content: assistantMsg.content, sender: 'assistant' }),
        });
      } else {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to get response from LLM');
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant', content: `Sorry Sir, there was an error: ${e.message}` }]);
    }
    setLoading(false);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Caspian AI Assistant</h1>
        <FileUpload authToken={authToken} />
      </div>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <p>{msg.content}</p>
          </div>
        ))}
        {loading && <div className="message assistant"><p>...</p></div>}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input-form" onSubmit={sendMessage}>
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message, Sir..."
          disabled={loading || !conversationId || !authToken}
        />
        <button type="submit" className="send-button" disabled={loading || !input.trim() || !conversationId || !authToken}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;