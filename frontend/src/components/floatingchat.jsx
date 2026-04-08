// fenora/frontend/src/components/FloatingChat.jsx
// ── Floating AI Chat Assistant ────────────────────────────────────
import { useState, useRef, useEffect } from "react";

const API = "http://localhost:5000";

const QUICK_PROMPTS = [
  { label: "Budget status?", key: "budget" },
  { label: "How to save more?", key: "reduce" },
  { label: "What to avoid?", key: "avoid" },
];

export default function FloatingChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hey! 👋 I'm your Fenora AI. Ask me anything about your spending, budget, or wardrobe.",
      time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [unread, setUnread] = useState(0);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setUnread(0);
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = {
      role: "user",
      text: text.trim(),
      time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question_key: text }),
      });
      const data = await res.json();
      const aiMsg = {
        role: "assistant",
        text: data.reply || "I couldn't process that. Please try again.",
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, aiMsg]);
      if (!open) setUnread((u) => u + 1);
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant",
        text: "Couldn't reach the server. Make sure you're logged in.",
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuick = (key) => {
    const labels = { budget: "Is my budget okay?", reduce: "How can I reduce spending?", avoid: "What should I avoid buying?" };
    sendMessage(key);
  };

  return (
    <>
      {/* Floating Button */}
      <div style={{ position: "fixed", bottom: 24, right: 24, zIndex: 1000 }}>
        {/* Chat window */}
        {open && (
          <div style={{
            position: "absolute", bottom: 70, right: 0,
            width: 340, maxHeight: 480,
            background: "#fff", borderRadius: 22,
            boxShadow: "0 16px 64px rgba(124,111,160,0.25), 0 4px 16px rgba(0,0,0,0.06)",
            border: "1px solid rgba(124,111,160,0.12)",
            display: "flex", flexDirection: "column",
            overflow: "hidden",
            animation: "chatOpen 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) both",
          }}>
            {/* Header */}
            <div style={{
              background: "linear-gradient(135deg, #7c6fa0, #a89cc8)",
              padding: "14px 18px",
              display: "flex", alignItems: "center", gap: 10,
            }}>
              <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>
                🤖
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>Fenora AI</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.7)" }}>
                  <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: "#6aff9a", marginRight: 4 }} />
                  Always here
                </div>
              </div>
              <button onClick={() => setOpen(false)} style={{ background: "rgba(255,255,255,0.15)", border: "none", borderRadius: "50%", width: 28, height: 28, color: "#fff", cursor: "pointer", fontSize: 14 }}>×</button>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "82%", padding: "10px 14px",
                    borderRadius: msg.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                    background: msg.role === "user" ? "linear-gradient(135deg, #7c6fa0, #a89cc8)" : "#f8f6ff",
                    color: msg.role === "user" ? "#fff" : "#3d3a52",
                    fontSize: 12, lineHeight: 1.6,
                    boxShadow: msg.role === "user" ? "0 2px 8px rgba(124,111,160,0.25)" : "0 1px 4px rgba(0,0,0,0.05)",
                  }}>
                    {msg.text}
                  </div>
                  <div style={{ fontSize: 9, color: "#b0aec8", marginTop: 3 }}>{msg.time}</div>
                </div>
              ))}
              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 4, padding: "8px 14px", background: "#f8f6ff", borderRadius: "18px 18px 18px 4px", maxWidth: "60px" }}>
                  {[0, 1, 2].map((i) => (
                    <div key={i} style={{ width: 6, height: 6, borderRadius: "50%", background: "#a89cc8", animation: `bounce 1.2s ease-in-out infinite`, animationDelay: `${i * 0.2}s` }} />
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Prompts */}
            <div style={{ padding: "8px 14px", display: "flex", gap: 6, flexWrap: "wrap", borderTop: "1px solid #f0eef8" }}>
              {QUICK_PROMPTS.map((p) => (
                <button key={p.key} onClick={() => handleQuick(p.key)} style={{
                  padding: "5px 12px", borderRadius: 100,
                  background: "#f0eef8", border: "none",
                  fontSize: 10, fontWeight: 600, color: "#7c6fa0",
                  cursor: "pointer", fontFamily: "inherit",
                  transition: "all 0.15s",
                }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#7c6fa0"; e.currentTarget.style.color = "#fff"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#f0eef8"; e.currentTarget.style.color = "#7c6fa0"; }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* Input */}
            <div style={{ padding: "10px 14px 14px", display: "flex", gap: 8, alignItems: "center" }}>
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
                placeholder="Ask anything…"
                style={{
                  flex: 1, padding: "10px 14px", borderRadius: 14,
                  border: "1.5px solid #e8e4f5", fontSize: 12,
                  color: "#1a1a2e", outline: "none", fontFamily: "inherit",
                  background: "#faf9ff",
                }}
              />
              <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} style={{
                width: 38, height: 38, borderRadius: "50%",
                background: input.trim() ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#f0eef8",
                border: "none", cursor: input.trim() ? "pointer" : "default",
                fontSize: 16, color: input.trim() ? "#fff" : "#b0aec8",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.2s", flexShrink: 0,
              }}>
                ↑
              </button>
            </div>
          </div>
        )}

        {/* FAB Button */}
        <button
          onClick={() => setOpen(!open)}
          style={{
            width: 56, height: 56, borderRadius: "50%",
            background: open ? "#7c6fa0" : "linear-gradient(135deg, #7c6fa0, #a89cc8)",
            border: "none", cursor: "pointer",
            boxShadow: "0 8px 24px rgba(124,111,160,0.4)",
            fontSize: 24, display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
            transform: open ? "rotate(0deg) scale(0.95)" : "rotate(0deg) scale(1)",
            position: "relative",
          }}
        >
          {open ? "×" : "🤖"}
          {unread > 0 && !open && (
            <div style={{
              position: "absolute", top: -2, right: -2,
              width: 18, height: 18, borderRadius: "50%",
              background: "#e07070", color: "#fff",
              fontSize: 10, fontWeight: 800,
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "2px solid #fff",
            }}>
              {unread}
            </div>
          )}
        </button>
      </div>

      <style>{`
        @keyframes chatOpen {
          from { opacity: 0; transform: scale(0.85) translateY(20px); transform-origin: bottom right; }
          to   { opacity: 1; transform: scale(1) translateY(0);       transform-origin: bottom right; }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
          40%            { transform: scale(1.2); opacity: 1; }
        }
      `}</style>
    </>
  );
}