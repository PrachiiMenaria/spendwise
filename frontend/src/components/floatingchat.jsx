// fenora/frontend/src/components/floatingchat.jsx — PHASE 3: Claude AI + "Can I Afford This?"
import { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

// ── Claude API caller ─────────────────────────────────────────────
async function callClaude(systemPrompt, userMessage) {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      system: systemPrompt,
      messages: [{ role: "user", content: userMessage }],
    }),
  });
  const data = await response.json();
  return data.content?.map(b => b.text || "").join("") || "";
}

const QUICK_PROMPTS = [
  { label: "Budget status?", key: "budget", emoji: "🎯" },
  { label: "Can I afford ₹2000?", key: "afford_2000", emoji: "💸" },
  { label: "How to save more?", key: "reduce", emoji: "✂️" },
  { label: "What to avoid?", key: "avoid", emoji: "🚫" },
];

export default function FloatingChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hey! 👋 I'm your Fenora AI. Ask me anything about your spending, budget, or wardrobe. Try asking 'Can I afford ₹3000?' for an instant answer!",
      time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [unread, setUnread] = useState(0);
  const [pulsing, setPulsing] = useState(true);
  const [showAffordModal, setShowAffordModal] = useState(false);
  const [affordAmount, setAffordAmount] = useState("");
  const [summaryData, setSummaryData] = useState(null);
  const [expenseSummary, setExpenseSummary] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Fetch user context in background
    const fetchContext = async () => {
      try {
        const [sum, exp] = await Promise.all([
          fetch(`${API}/api/get-summary`, { credentials: "include" }).then(r => r.json()).catch(() => null),
          fetch(`${API}/api/expense-summary`, { credentials: "include" }).then(r => r.json()).catch(() => null),
        ]);
        setSummaryData(sum);
        setExpenseSummary(exp);
      } catch {}
    };
    fetchContext();
  }, []);

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

  const buildSystemPrompt = () => {
    const budget = summaryData?.budget || 0;
    const spent = summaryData?.this_month_total || 0;
    const remaining = summaryData?.remaining || 0;
    const pctUsed = budget > 0 ? Math.round((spent / budget) * 100) : 0;
    const cats = expenseSummary?.category_totals || {};
    const topCat = Object.entries(cats).sort((a, b) => b[1] - a[1])[0];
    const neverWorn = summaryData?.never_worn_count || 0;
    const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
    const dayOfMonth = new Date().getDate();
    const dailyBurnRate = dayOfMonth > 0 ? spent / dayOfMonth : 0;
    const projectedMonthly = dailyBurnRate * daysInMonth;
    const daysRemainingInMonth = daysInMonth - dayOfMonth;

    return `You are Fenora AI — a witty, sharp financial advisor for a Gen Z user in India. You're like a smart friend who knows finance.

USER DATA (real-time):
- Monthly Budget: ₹${budget.toLocaleString("en-IN")}
- Spent This Month: ₹${spent.toLocaleString("en-IN")} (${pctUsed}%)
- Remaining Budget: ₹${remaining.toLocaleString("en-IN")}
- Days Left in Month: ${daysRemainingInMonth}
- Daily Burn Rate: ₹${Math.round(dailyBurnRate).toLocaleString("en-IN")}/day
- Projected Month-End Spend: ₹${Math.round(projectedMonthly).toLocaleString("en-IN")}
- Top Category: ${topCat ? `${topCat[0]} (₹${Number(topCat[1]).toLocaleString("en-IN")})` : "No data"}
- Unworn Wardrobe Items: ${neverWorn}

RULES:
- Max 100 words per response
- Be direct, helpful, slightly playful
- For "can I afford X?" questions: compare X to remaining budget, factor in remaining days, give CLEAR yes/no + reasoning
- Use ₹ with Indian number formatting
- Never say "as an AI" or "I don't have access to"
- If user types a number like "can I afford 2000" or "afford ₹2000", treat it as affordability question`;
  };

  const detectAffordabilityQuery = (text) => {
    const patterns = [
      /can i afford[^₹\d]*[₹]?\s*(\d+)/i,
      /afford[^₹\d]*[₹]?\s*(\d+)/i,
      /is[^₹\d]*[₹]?\s*(\d+)[^₹\d]*(too expensive|okay|fine|good)/i,
      /should i buy[^₹\d]*[₹]?\s*(\d+)/i,
      /[₹]?\s*(\d+)[^₹\d]*(affordable|too much|okay to buy)/i,
    ];
    for (const p of patterns) {
      const m = text.match(p);
      if (m) return parseInt(m[1]);
    }
    return null;
  };

  const buildAffordabilityMessage = (amount) => {
    const remaining = summaryData?.remaining || 0;
    const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
    const dayOfMonth = new Date().getDate();
    const daysLeft = daysInMonth - dayOfMonth;
    const spent = summaryData?.this_month_total || 0;
    const dailyBurn = dayOfMonth > 0 ? spent / dayOfMonth : 0;
    const projectedSpend = dailyBurn * daysLeft;

    return `Can I afford ₹${amount.toLocaleString("en-IN")}?

Context:
- Remaining budget: ₹${remaining.toLocaleString("en-IN")}
- Item cost: ₹${amount.toLocaleString("en-IN")}
- After buying: ₹${(remaining - amount).toLocaleString("en-IN")} left
- Days left in month: ${daysLeft}
- Projected other spending for rest of month (at current rate): ₹${Math.round(projectedSpend).toLocaleString("en-IN")}
- Buffer after item + projected spend: ₹${Math.round(remaining - amount - projectedSpend).toLocaleString("en-IN")}

Give a clear YES or NO answer with specific reasoning. Be honest even if the answer is no.`;
  };

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
      const systemPrompt = buildSystemPrompt();
      const affordAmount = detectAffordabilityQuery(text);
      const messageToSend = affordAmount ? buildAffordabilityMessage(affordAmount) : text;

      let reply = "";
      try {
        reply = await callClaude(systemPrompt, messageToSend);
      } catch (err) {
        console.error("Chat backend fallback error:", err);
        // Fallback to backend
        const res = await fetch(`${API}/api/smart-chat`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          credentials: "include", body: JSON.stringify({ message: text }),
        });
        if (!res.ok) throw new Error("Fallback API failed: " + res.status);
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        reply = data.reply || "Couldn't process that. Please try again.";
      }

      const aiMsg = {
        role: "assistant", text: reply,
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages(prev => [...prev, aiMsg]);
      if (!open) setUnread(u => u + 1);
    } catch (err) {
      console.error("Total chat failure:", err);
      setMessages(prev => [...prev, {
        role: "assistant",
        text: "Couldn't reach the server. Make sure you're logged in.",
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAffordCheck = async () => {
    const amt = parseInt(affordAmount);
    if (!amt || amt <= 0) return;
    setShowAffordModal(false);
    setAffordAmount("");
    await sendMessage(`Can I afford ₹${amt}?`);
    if (!open) setOpen(true);
  };

  return (
    <>
      {/* Can I Afford Modal (outside chat) */}
      {showAffordModal && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 1001,
          background: "rgba(0,0,0,0.3)", backdropFilter: "blur(4px)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }} onClick={e => { if (e.target === e.currentTarget) setShowAffordModal(false); }}>
          <div style={{
            background: "#fff", borderRadius: 20, padding: "28px 28px 24px",
            width: "min(360px, 90vw)",
            boxShadow: "0 20px 60px rgba(107,95,160,0.2)",
            border: "1px solid rgba(107,95,160,0.1)",
            animation: "affordOpen 0.28s cubic-bezier(0.175, 0.885, 0.32, 1.275) both",
          }}>
            <div style={{ fontSize: 32, marginBottom: 10, textAlign: "center" }}>💸</div>
            <h3 style={{ margin: "0 0 6px", fontSize: 17, fontWeight: 800, color: "#1a1a2e", textAlign: "center" }}>Can I Afford This?</h3>
            <p style={{ fontSize: 12, color: "#9898b8", textAlign: "center", margin: "0 0 20px" }}>
              {summaryData ? `₹${(summaryData.remaining || 0).toLocaleString("en-IN")} left this month` : "Enter an amount to check"}
            </p>
            <div style={{ display: "flex", gap: 8 }}>
              <div style={{ position: "relative", flex: 1 }}>
                <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", fontSize: 13, color: "#6d4fc2", fontWeight: 700 }}>₹</span>
                <input
                  autoFocus
                  type="number"
                  placeholder="e.g. 2000"
                  value={affordAmount}
                  onChange={e => setAffordAmount(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter") handleAffordCheck(); }}
                  style={{
                    width: "100%", padding: "12px 12px 12px 28px", borderRadius: 12,
                    border: "1.5px solid #e8e4f5", fontSize: 14, fontWeight: 700, color: "#1a1a2e",
                    outline: "none", fontFamily: "inherit", background: "#faf8ff",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <button onClick={handleAffordCheck} style={{
                background: "linear-gradient(135deg, #6d4fc2, #9577e0)",
                color: "#fff", border: "none", borderRadius: 12,
                padding: "12px 18px", fontSize: 13, fontWeight: 700,
                cursor: "pointer", fontFamily: "inherit",
                boxShadow: "0 4px 14px rgba(109,79,194,0.32)",
              }}>Ask AI</button>
            </div>
            <button onClick={() => setShowAffordModal(false)} style={{
              display: "block", width: "100%", marginTop: 10,
              background: "none", border: "none", fontSize: 12, color: "#b0aec8",
              cursor: "pointer", fontFamily: "inherit", padding: "4px",
            }}>Cancel</button>
          </div>
        </div>
      )}

      <div style={{ position: "fixed", bottom: 24, right: 24, zIndex: 1000 }}>
        {/* Chat Window */}
        {open && (
          <div style={{
            position: "absolute", bottom: 72, right: 0,
            width: 348, maxHeight: 520,
            background: "#fff", borderRadius: 24,
            boxShadow: "0 20px 72px rgba(107,95,160,0.28), 0 4px 20px rgba(0,0,0,0.06)",
            border: "1px solid rgba(107,95,160,0.12)",
            display: "flex", flexDirection: "column", overflow: "hidden",
            animation: "chatOpen 0.32s cubic-bezier(0.175, 0.885, 0.32, 1.275) both",
          }}>
            {/* Header */}
            <div style={{
              background: "linear-gradient(135deg, #2d1b69, #6d4fc2)",
              padding: "15px 17px",
              display: "flex", alignItems: "center", gap: 11,
            }}>
              <div style={{
                width: 38, height: 38, borderRadius: 11,
                background: "rgba(255,255,255,0.16)", backdropFilter: "blur(8px)",
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 19,
                border: "1px solid rgba(255,255,255,0.22)",
              }}>🤖</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13.5, fontWeight: 700, color: "#fff" }}>Fenora AI</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.68)", display: "flex", alignItems: "center", gap: 5 }}>
                  <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#6affa0", display: "inline-block" }} />
                  Claude-powered · Always here
                </div>
              </div>
              {/* Afford button in header */}
              <button onClick={() => { setShowAffordModal(true); }} style={{
                background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.22)",
                borderRadius: 100, padding: "5px 10px", color: "#fff",
                cursor: "pointer", fontSize: 10, fontWeight: 700, fontFamily: "inherit",
                transition: "background 0.15s", whiteSpace: "nowrap",
              }}
                title="Check if you can afford something"
                onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.28)"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.15)"}
              >💸 Afford?</button>
              <button onClick={() => setOpen(false)} style={{
                background: "rgba(255,255,255,0.13)", border: "1px solid rgba(255,255,255,0.18)",
                borderRadius: "50%", width: 28, height: 28, color: "#fff",
                cursor: "pointer", fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center",
                transition: "background 0.15s", flexShrink: 0,
              }}
                onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.25)"}
                onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.13)"}
              >×</button>
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto", padding: "13px 14px", display: "flex", flexDirection: "column", gap: 9, background: "#faf8ff" }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "84%", padding: "9px 13px",
                    borderRadius: msg.role === "user" ? "18px 18px 5px 18px" : "18px 18px 18px 5px",
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #6d4fc2, #9577e0)"
                      : "#fff",
                    color: msg.role === "user" ? "#fff" : "#3d3a52",
                    fontSize: 12.5, lineHeight: 1.6, fontWeight: 500,
                    boxShadow: msg.role === "user" ? "0 3px 10px rgba(109,79,194,0.28)" : "0 2px 8px rgba(107,95,160,0.06)",
                    border: msg.role === "assistant" ? "1px solid rgba(107,95,160,0.09)" : "none",
                  }}>
                    {msg.text}
                  </div>
                  <div style={{ fontSize: 9, color: "#b0aec8", marginTop: 3 }}>{msg.time}</div>
                </div>
              ))}

              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "9px 13px", background: "#fff", borderRadius: "18px 18px 18px 5px", width: "fit-content", border: "1px solid rgba(107,95,160,0.09)", boxShadow: "0 2px 8px rgba(107,95,160,0.06)" }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#9577e0", animation: "bounceFC 1.2s ease-in-out infinite", animationDelay: `${i * 0.2}s` }} />
                  ))}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick prompts */}
            <div style={{ padding: "7px 12px", display: "flex", gap: 5, flexWrap: "wrap", borderTop: "1px solid #f0edf8", background: "#fff" }}>
              {QUICK_PROMPTS.map(p => (
                <button key={p.key} onClick={() => sendMessage(p.key === "afford_2000" ? "Can I afford ₹2000?" : p.key)} style={{
                  padding: "4px 10px", borderRadius: 100,
                  background: "#f0edf8", border: "1px solid rgba(109,79,194,0.12)",
                  fontSize: 10, fontWeight: 600, color: "#6d4fc2",
                  cursor: "pointer", fontFamily: "inherit", transition: "all 0.15s",
                  display: "flex", alignItems: "center", gap: 3,
                }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#6d4fc2"; e.currentTarget.style.color = "#fff"; e.currentTarget.style.borderColor = "#6d4fc2"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#f0edf8"; e.currentTarget.style.color = "#6d4fc2"; e.currentTarget.style.borderColor = "rgba(109,79,194,0.12)"; }}
                >
                  {p.emoji} {p.label}
                </button>
              ))}
            </div>

            {/* Input */}
            <div style={{ padding: "9px 12px 13px", display: "flex", gap: 7, alignItems: "center", background: "#fff" }}>
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
                placeholder="Ask anything or 'Can I afford ₹X?'"
                style={{
                  flex: 1, padding: "9px 13px", borderRadius: 13,
                  border: "1.5px solid #ebe8f5", fontSize: 12, color: "#18182e",
                  outline: "none", fontFamily: "inherit", background: "#faf8ff",
                  transition: "border 0.15s",
                }}
                onFocus={e => e.target.style.borderColor = "#6d4fc2"}
                onBlur={e => e.target.style.borderColor = "#ebe8f5"}
              />
              <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()} style={{
                width: 38, height: 38, borderRadius: "50%",
                background: input.trim() ? "linear-gradient(135deg, #6d4fc2, #9577e0)" : "#f0edf8",
                border: "none", cursor: input.trim() ? "pointer" : "default",
                fontSize: 16, color: input.trim() ? "#fff" : "#b0aec8",
                display: "flex", alignItems: "center", justifyContent: "center",
                transition: "all 0.2s", flexShrink: 0,
                boxShadow: input.trim() ? "0 3px 10px rgba(109,79,194,0.28)" : "none",
              }}>↑</button>
            </div>
          </div>
        )}

        {/* "Can I Afford?" quick-launch button (visible when chat closed) */}
        {!open && (
          <div style={{ position: "absolute", bottom: 68, right: 0, display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end" }}>
            <button
              onClick={() => setShowAffordModal(true)}
              style={{
                background: "linear-gradient(135deg, #f0803c, #e05c7d)",
                border: "none", borderRadius: 100, padding: "9px 16px",
                color: "#fff", fontSize: 11.5, fontWeight: 700, cursor: "pointer",
                fontFamily: "inherit", boxShadow: "0 4px 16px rgba(240,128,60,0.35)",
                display: "flex", alignItems: "center", gap: 6,
                animation: "slideInFC 0.4s ease both",
                whiteSpace: "nowrap",
              }}
            >
              💸 Can I afford this?
            </button>
          </div>
        )}

        {/* FAB */}
        <button
          onClick={() => setOpen(!open)}
          style={{
            width: 56, height: 56, borderRadius: "50%",
            background: open ? "#6d4fc2" : "linear-gradient(135deg, #2d1b69, #6d4fc2)",
            border: "none", cursor: "pointer",
            boxShadow: "0 8px 28px rgba(109,79,194,0.45)",
            fontSize: 23, display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
            transform: open ? "scale(0.92)" : "scale(1)",
            position: "relative",
            animation: pulsing ? "pulseFC 2.5s infinite" : "none",
          }}
        >
          <span style={{ transition: "transform 0.25s", transform: open ? "rotate(90deg)" : "rotate(0deg)", lineHeight: 1 }}>
            {open ? "×" : "🤖"}
          </span>
          {unread > 0 && !open && (
            <div style={{
              position: "absolute", top: -3, right: -3,
              width: 19, height: 19, borderRadius: "50%",
              background: "#e05c7d", color: "#fff",
              fontSize: 9.5, fontWeight: 800, border: "2px solid #fff",
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
        @keyframes affordOpen {
          from { opacity:0; transform:scale(0.88) translateY(12px); }
          to   { opacity:1; transform:scale(1) translateY(0); }
        }
        @keyframes slideInFC {
          from { opacity:0; transform:translateX(10px); }
          to   { opacity:1; transform:translateX(0); }
        }
        @keyframes bounceFC {
          0%,80%,100%{ transform:scale(0.75); opacity:0.4; }
          40%{ transform:scale(1.2); opacity:1; }
        }
        @keyframes pulseFC {
          0%,100%{ box-shadow: 0 8px 28px rgba(109,79,194,0.45), 0 0 0 0 rgba(109,79,194,0.35); }
          50%{ box-shadow: 0 8px 28px rgba(109,79,194,0.45), 0 0 0 14px rgba(109,79,194,0); }
        }
      `}</style>
    </>
  );
}