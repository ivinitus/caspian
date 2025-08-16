import React, { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [user, setUser] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello Sir, I am Caspian. How may I assist you today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Use default personal user seeded on backend
    const username = import.meta.env.VITE_DEFAULT_USERNAME || "sir";
    setUser({ id: 1, username });
  }, []);

  useEffect(() => {
    if (!user || conversationId) return;
    // Start a conversation for the user
    (async () => {
      try {
        const res = await fetch(`${API_URL}/conversations/?user_id=1`, { method: "POST" });
        const data = await res.json();
        setConversationId(data.id);
      } catch (e) {
        // ignore
      }
    })();
  }, [user, conversationId]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || !conversationId) return;

    const userMsg = { role: "user", content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setLoading(true);
    setInput("");

    try {
      // save message to backend
      await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: userMsg.content, sender: userMsg.role }),
      });

      // ask LLM
      const res = await fetch(`${API_URL}/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });
      const data = await res.json();
      const reply = data.text || data.reply || "Sorry Sir, I could not process that.";

      const assistantMsg = { role: "assistant", content: reply };
      setMessages([...newMessages, assistantMsg]);

      // save assistant message
      await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: assistantMsg.content, sender: assistantMsg.role }),
      });
    } catch {
      setMessages([...newMessages, { role: "assistant", content: "Sorry Sir, there was an error." }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>Caspian AI Assistant</h2>
      {!conversationId && <div>Initializing conversation…</div>}
      <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16, minHeight: 300, background: "#fafbfc" }}>
        {messages.map((m, i) => (
          <div key={i} style={{ margin: "8px 0", textAlign: m.role === "user" ? "right" : "left" }}>
            <b>{m.role === "user" ? "You" : "Caspian"}:</b> {m.content}
          </div>
        ))}
        {loading && <div><i>Caspian is typing…</i></div>}
      </div>
      <form onSubmit={sendMessage} style={{ display: "flex", marginTop: 12 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message, Sir…"
          style={{ flex: 1, padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          disabled={loading || !conversationId}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim() || !conversationId} style={{ marginLeft: 8, padding: "8px 16px" }}>
          Send
        </button>
      </form>
    </div>
  );
}