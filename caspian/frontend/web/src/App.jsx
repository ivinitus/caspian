import React, { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello Sir, I am Caspian. How may I assist you today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { role: "user", content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setLoading(true);
    setInput("");
    try {
      const res = await fetch(`${API_URL}/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });
      const data = await res.json();
      const reply =
        data.reply ||
        data.choices?.[0]?.message?.content ||
        "Sorry Sir, I could not process that.";
      setMessages([...newMessages, { role: "assistant", content: reply }]);
    } catch {
      setMessages([...newMessages, { role: "assistant", content: "Sorry Sir, there was an error." }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>Caspian AI Assistant</h2>
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
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()} style={{ marginLeft: 8, padding: "8px 16px" }}>
          Send
        </button>
      </form>
    </div>
  );
}