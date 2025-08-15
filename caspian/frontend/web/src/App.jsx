import React, { useState, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hello Sir, I am Caspian. How may I assist you today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
    <div style={{ minHeight: "100vh", background: "#f4f6fa", display: "flex", flexDirection: "column" }}>
      <header style={{ background: "#1a2233", color: "#fff", padding: "20px 0", textAlign: "center", fontSize: 28, fontWeight: 700, letterSpacing: 1 }}>
        Caspian AI Assistant
      </header>
      <main style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-start", padding: 0 }}>
        <div style={{ width: "100%", maxWidth: 600, margin: "32px 0 0 0", background: "#fff", borderRadius: 12, boxShadow: "0 2px 12px #0001", padding: 0, display: "flex", flexDirection: "column", minHeight: 400 }}>
          <div style={{ flex: 1, overflowY: "auto", padding: 24, paddingBottom: 0, maxHeight: 500 }}>
            {messages.map((m, i) => (
              <div key={i} style={{
                margin: "12px 0",
                textAlign: m.role === "user" ? "right" : "left",
                display: "flex",
                flexDirection: m.role === "user" ? "row-reverse" : "row",
                alignItems: "flex-end"
              }}>
                <div style={{
                  background: m.role === "user" ? "#e0e7ff" : "#f1f5f9",
                  color: "#222",
                  borderRadius: 16,
                  padding: "10px 16px",
                  maxWidth: "80%",
                  fontSize: 16,
                  boxShadow: m.role === "user" ? "0 1px 4px #a5b4fc55" : "0 1px 4px #cbd5e155"
                }}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && <div style={{ margin: "12px 0", color: "#888" }}><i>Caspian is typing…</i></div>}
            <div ref={chatEndRef} />
          </div>
          <form onSubmit={sendMessage} style={{ display: "flex", borderTop: "1px solid #e5e7eb", padding: 16, background: "#f8fafc", borderRadius: "0 0 12px 12px" }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message, Sir…"
              style={{ flex: 1, padding: 12, borderRadius: 8, border: "1px solid #cbd5e1", fontSize: 16, background: "#fff" }}
              disabled={loading}
              autoFocus
            />
            <button type="submit" disabled={loading || !input.trim()} style={{ marginLeft: 12, padding: "12px 24px", borderRadius: 8, background: "#6366f1", color: "#fff", border: "none", fontWeight: 600, fontSize: 16, cursor: loading ? "not-allowed" : "pointer" }}>
              Send
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}