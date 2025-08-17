import { useState, useEffect, useRef } from 'react';
import './App.css';

const API_URL = '/api';

function FileUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/rag/upload`, {
        method: 'POST',
        // You'll need to handle auth in a real app
        // headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Successfully uploaded ${data.filename}`);
      } else {
        throw new Error('Upload failed');
      }
    } catch (e) {
      setMessage('Upload failed');
    }
    setUploading(false);
  };

  return (
    <div className="file-upload">
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
      {message && <p>{message}</p>}
    </div>
  );
}


function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello Sir, I am Caspian. How may I assist you today?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const startConversation = async () => {
      try {
        const res = await fetch(`${API_URL}/conversations/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'sir' }),
        });
        if (res.ok) {
          const data = await res.json();
          setConversationId(data.id);
        } else {
          throw new Error('Failed to start conversation');
        }
      } catch (e) {
        console.error("Failed to start conversation:", e);
        setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry Sir, I could not connect to the server.' }]);
      }
    };
    startConversation();
  }, []);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !conversationId) return;

    const userMsg = { role: 'user', content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: userMsg.content, sender: 'user' }),
      });

      const res = await fetch(`${API_URL}/llm/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages.map(({role, content}) => ({role, content})) }),
      });

      if (res.ok) {
        const data = await res.json();
        const reply = data.text || 'Sorry Sir, I could not process that.';
        const assistantMsg = { role: 'assistant', content: reply };
        
        setMessages(prev => [...prev, assistantMsg]);

        await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: assistantMsg.content, sender: 'assistant' }),
        });
      } else {
        throw new Error('Failed to get response from LLM');
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry Sir, there was an error.' }]);
    }
    setLoading(false);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Caspian</h1>
        <FileUpload />
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
          disabled={loading || !conversationId}
        />
        <button type="submit" className="send-button" disabled={loading || !input.trim() || !conversationId}>
          Send
        </button>
      </form>
    </div>
  );
}

export default App;