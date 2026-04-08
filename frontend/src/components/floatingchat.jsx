// fenora/frontend/src/components/floatingchat.jsx — UPGRADED
import { useState, useRef, useEffect } from "react";

const API = "http://localhost:5000";

const QUICK_PROMPTS = [
  { label: "Budget status?", key: "budget", emoji: "🎯" },
  { label: "Reduce spending?", key: "reduce", emoji: "✂️" },
  { label: "What to avoid?", key: "avoid", emoji: "🚫" },
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
  const [pulsing, setPulsing] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setUnread(0);
      setPulsing(false);
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;
    const userMsg = {
      role: "user", text: text.trim(),
      time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        credentials: "include", body: JSON.stringify({ question_key: text }),
      });
      const data = await res.json();
      const aiMsg = {
        role: "assistant",
        text: data.reply || "I couldn't process that. Please try again.",
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages(prev => [...prev, aiMsg]);
      if (!open) setUnread(u => u + 1);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        text: "Couldn't reach the server. Make sure you're logged in.",
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div style={{ position: "fixed", bottom: 24, right: 24, zIndex: 1000 }}>
        {/* Chat Window */}
        {open && (
          <div style={{
            position: "absolute", bottom: 72, right: 0,
            width: 348, maxHeight: 500,
            background: "#fff", borderRadius: 24,
            boxShadow: "0 20px 72px rgba(107,95,160,0.28), 0 4px 20px rgba(0,0,0,0.06)",
            border: "1px solid rgba(107,95,160,0.12)",
            display: "flex", flexDirection: "column", overflow: "hidden",
            animation: "chatOpen 0.32s cubic-bezier(0.175, 0.885, 0.32, 1.275) both",
          }}>
            {/* Header */}
            <div style={{
              background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
              padding: "16px 18px",
              display: "flex", alignItems: "center", gap: 12,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 12,
                background: "rgba(255,255,255,0.18)", backdropFilter: "blur(8px)",
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20,
                border: "1px solid rgba(255,255,255,0.25)",
              }}>🤖</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#fff" }}>Fenora AI</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.7)", display: "flex", alignItems: "center", gap: 5 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#6affa0", display: "inline-block", boxShadow: "0 0 6px rgba(106,255,160,0.7)" }} />
                  Always here for you
                </div>
              </div>
              <button onClick={() => setOpen(false)} style={{
                background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.2)",
                borderRadius: "50%", width: 30, height: 30, color: "#fff",
                cursor: "pointer", fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s",
              }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.25)"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.15)"}
              >×</button>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10, background: "#faf9ff" }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "84%", padding: "10px 14px",
                    borderRadius: msg.role === "user" ? "18px 18px 5px 18px" : "18px 18px 18px 5px",
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #6b5fa0, #9b8ec8)"
                      : "#fff",
                    color: msg.role === "user" ? "#fff" : "#3d3a52",
                    fontSize: 12.5, lineHeight: 1.6, fontWeight: 500,
                    boxShadow: msg.role === "user"
                      ? "0 3px 10px rgba(107,95,160,0.3)"
                      : "0 2px 8px rgba(107,95,160,0.06)",
                    border: msg.role === "assistant" ? "1px solid rgba(107,95,160,0.08)" : "none",
                  }}>
                    {msg.text}
                  </div>
                  <div style={{ fontSize: 9, color: "#b0aec8", marginTop: 3 }}>{msg.time}</div>
                </div>
              ))}

              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "10px 14px", background: "#fff", borderRadius: "18px 18px 18px 5px", width: "fit-content", border: "1px solid rgba(107,95,160,0.08)", boxShadow: "0 2px 8px rgba(107,95,160,0.06)" }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#9b8ec8", animation: "bounce 1.2s ease-in-out infinite", animationDelay: `${i * 0.2}s` }} />
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick prompts */}
            <div style={{ padding: "8px 14px", display: "flex", gap: 6, flexWrap: "wrap", borderTop: "1px solid #f0eef8", background: "#fff" }}>
              {QUICK_PROMPTS.map(p => (
                <button key={p.key} onClick={() => sendMessage(p.key)} style={{
                  padding: "5px 11px", borderRadius: 100,
                  background: "#f5f3fc", border: "1px solid rgba(107,95,160,0.12)",
                  fontSize: 10.5, fontWeight: 600, color: "#6b5fa0",
                  cursor: "pointer", fontFamily: "inherit", transition: "all 0.15s",
                  display: "flex", alignItems: "center", gap: 4,
                }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#6b5fa0"; e.currentTarget.style.color = "#fff"; e.currentTarget.style.borderColor = "#6b5fa0"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#f5f3fc"; e.currentTarget.style.color = "#6b5fa0"; e.currentTarget.style.borderColor = "rgba(107,95,160,0.12)"; }}
                >
                  {p.emoji} {p.label}
                </button>
              ))}
            </div>

            {/* Input */}
            <div style={{ padding: "10px 14px 14px", display: "flex", gap: 8, alignItems: "center", background: "#fff" }}>
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
                placeholder="Ask anything…"
                style={{
                  flex: 1, padding: "10px 14px", borderRadius: 14,
                  border: "1.5px solid #ebe8f5", fontSize: 12.5, color: "#18182e",
                  outline: "none", fontFamily: "inherit", background: "#faf9ff",
                  transition: "border 0.15s",
                }}
                onFocus={e => e.target.style.borderColor = "#6b5fa0"}
                onBlur={e => e.target.style.borderColor = "#ebe8f5"}
              />
              <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} style={{
                width: 40, height: 40, borderRadius: "50%",
                background: input.trim() ? "linear-gradient(135deg, #6b5fa0, #9b8ec8)" : "#f0eef8",
                border: "none", cursor: input.trim() ? "pointer" : "default",
                fontSize: 17, color: input.trim() ? "#fff" : "#b0aec8",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.2s", flexShrink: 0,
                boxShadow: input.trim() ? "0 3px 10px rgba(107,95,160,0.3)" : "none",
              }}>↑</button>
            </div>
          </div>
        )}

        {/* FAB */}
        <button
          onClick={() => setOpen(!open)}
          style={{
            width: 58, height: 58, borderRadius: "50%",
            background: open ? "#6b5fa0" : "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
            border: "none", cursor: "pointer",
            boxShadow: pulsing
              ? "0 8px 28px rgba(107,95,160,0.45), 0 0 0 0 rgba(107,95,160,0.4)"
              : "0 8px 28px rgba(107,95,160,0.45)",
            fontSize: 24, display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
            transform: open ? "scale(0.92)" : "scale(1)",
            position: "relative",
            animation: pulsing ? "pulse 2.5s infinite" : "none",
          }}
        >
          <span style={{ transition: "transform 0.25s", transform: open ? "rotate(90deg)" : "rotate(0deg)", fontSize: open ? 26 : 24, lineHeight: 1 }}>
            {open ? "×" : "🤖"}
          </span>
          {unread > 0 && !open && (
            <div style={{
              position: "absolute", top: -2, right: -2,
              width: 20, height: 20, borderRadius: "50%",
              background: "#d96b6b", color: "#fff",
              fontSize: 10, fontWeight: 800, border: "2px solid #fff",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>{unread}</div>
          )}
        </button>
      </div>

      <style>{`
        @keyframes chatOpen {
          from { opacity:0; transform:scale(0.85) translateY(20px); transform-origin:bottom right; }
          to   { opacity:1; transform:scale(1) translateY(0); transform-origin:bottom right; }
        }
        @keyframes bounce {
          0%,80%,100%{ transform:scale(0.75); opacity:0.4; }
          40%{ transform:scale(1.2); opacity:1; }
        }
        @keyframes pulse {
          0%,100%{ box-shadow: 0 8px 28px rgba(107,95,160,0.45), 0 0 0 0 rgba(107,95,160,0.35); }
          50%{ box-shadow: 0 8px 28px rgba(107,95,160,0.45), 0 0 0 14px rgba(107,95,160,0); }
        }
      `}</style>
    </>
  );
}